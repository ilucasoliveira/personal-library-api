"""Prepara o banco da demo pública: cria as tabelas, zera os livros e insere os exemplos.

Uso (com o .env apontando para o banco da DEMO, nunca para o banco pessoal):
    poetry run python -m back_end_library.seed_demo

As capas vêm do Google Books (use GOOGLE_BOOKS_KEY para não esbarrar na cota)
e, se ele falhar, da Open Library. Sem capa, o front mostra a capa colorida padrão.
"""
import os
from datetime import date, timedelta

import httpx
from sqlalchemy import text

from .config import DEMO_MODE
from .database import SessionLocal, engine
from .models import Base, Book, Profile

TODAY = date.today()
# opcional: com a chave, o Google Books não barra por cota
GOOGLE_BOOKS_KEY = os.getenv("GOOGLE_BOOKS_KEY")


def days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


# Livros de exemplo: sinopses e comentários escritos para a demo.
EXAMPLES = [
    {
        "title": "Dom Casmurro",
        "author": "Machado de Assis",
        "gender": "Romance",
        "synopsis": "Bento Santiago revisita a própria vida para tentar entender o amor por Capitu e a desconfiança que tomou conta dele. Um narrador nada confiável conta a história do jeito que lhe convém.",
        "grade": 5,
        "comment": "Até hoje não sei o que pensar da Capitu.",
        "reading_status": "read",
        "favorite": True,
        "finished": 40,
        "added": 120,
    },
    {
        "title": "O Hobbit",
        "author": "J.R.R. Tolkien",
        "gender": "Fantasia",
        "synopsis": "Bilbo Bolseiro só queria sossego na sua toca, mas um mago e treze anões o arrastam para uma viagem até uma montanha guardada por um dragão.",
        "grade": 5,
        "comment": "A melhor porta de entrada para a Terra-média.",
        "reading_status": "read",
        "favorite": True,
        "finished": 12,
        "added": 90,
    },
    {
        "title": "1984",
        "author": "George Orwell",
        "gender": "Distopia",
        "synopsis": "Num Estado que vigia cada gesto e reescreve o passado, Winston Smith começa a duvidar do Partido e arrisca tudo por um pouco de verdade.",
        "grade": 4,
        "comment": "Assustadoramente atual.",
        "reading_status": "read",
        "favorite": False,
        "finished": 75,
        "added": 150,
    },
    {
        "title": "O Pequeno Príncipe",
        "author": "Antoine de Saint-Exupéry",
        "gender": "Fábula",
        "synopsis": "Um aviador perdido no deserto conhece um pequeno príncipe vindo de outro planeta, que conta suas viagens e o que aprendeu sobre amizade e cuidado.",
        "grade": 5,
        "comment": None,
        "reading_status": "read",
        "favorite": True,
        "finished": 200,
        "added": 210,
    },
    {
        "title": "A Revolução dos Bichos",
        "author": "George Orwell",
        "gender": "Sátira",
        "synopsis": "Os animais de uma fazenda expulsam o dono e prometem igualdade para todos, até que alguns passam a ser mais iguais que os outros.",
        "grade": 4,
        "comment": None,
        "reading_status": "read",
        "favorite": False,
        "finished": 5,
        "added": 30,
    },
    {
        "title": "Memórias Póstumas de Brás Cubas",
        "author": "Machado de Assis",
        "gender": "Romance",
        "synopsis": "Um defunto autor decide contar a própria vida depois de morto, com ironia e sem pressa, rindo das vaidades da sociedade e das suas próprias.",
        "grade": 4,
        "comment": "A primeira frase já vale o livro.",
        "reading_status": "read",
        "favorite": False,
        "finished": 100,
        "added": 130,
    },
    {
        "title": "Orgulho e Preconceito",
        "author": "Jane Austen",
        "gender": "Romance",
        "synopsis": "Elizabeth Bennet e o orgulhoso Sr. Darcy começam com o pé esquerdo e precisam rever as primeiras impressões que tiveram um do outro.",
        "grade": None,
        "comment": None,
        "reading_status": "reading",
        "favorite": False,
        "finished": None,
        "added": 8,
    },
    {
        "title": "Duna",
        "author": "Frank Herbert",
        "gender": "Ficção científica",
        "synopsis": "No planeta desértico de Arrakis, fonte da especiaria mais valiosa do universo, o jovem Paul Atreides se vê no centro de uma disputa entre casas nobres.",
        "grade": None,
        "comment": None,
        "reading_status": "reading",
        "favorite": True,
        "finished": None,
        "added": 15,
    },
    {
        "title": "Cem Anos de Solidão",
        "author": "Gabriel García Márquez",
        "gender": "Realismo mágico",
        # em português nenhuma das APIs acha a capa; busca pelo título original
        "cover_title": "Cien años de soledad",
        "synopsis": "A história de sete gerações da família Buendía na cidade de Macondo, onde o extraordinário acontece com a maior naturalidade.",
        "grade": None,
        "comment": None,
        "reading_status": "toRead",
        "favorite": False,
        "finished": None,
        "added": 20,
    },
    {
        "title": "Frankenstein",
        "author": "Mary Shelley",
        "gender": "Terror",
        "synopsis": "Victor Frankenstein dá vida a uma criatura e foge do que criou. Abandonada, ela parte em busca de respostas e de vingança.",
        "grade": None,
        "comment": None,
        "reading_status": "toRead",
        "favorite": False,
        "finished": None,
        "added": 25,
    },
    {
        "title": "A Hora da Estrela",
        "author": "Clarice Lispector",
        "gender": "Romance",
        "synopsis": "Um narrador tenta contar a vida de Macabéa, uma nordestina que vive no Rio de Janeiro quase sem perceber a si mesma.",
        "grade": None,
        "comment": None,
        "reading_status": "toRead",
        "favorite": False,
        "finished": None,
        "added": 3,
    },
    {
        "title": "Fahrenheit 451",
        "author": "Ray Bradbury",
        "gender": "Distopia",
        "synopsis": "Guy Montag é um bombeiro cujo trabalho é queimar livros, até que uma vizinha curiosa o faz perguntar o que existe dentro deles.",
        "grade": None,
        "comment": None,
        "reading_status": "toRead",
        "favorite": False,
        "finished": None,
        "added": 1,
    },
]


def google_books_cover(client: httpx.Client, title: str, author: str) -> str | None:
    """Capa pelo Google Books. Sem chave, a cota anônima costuma estourar (erro 429)."""
    params = {"q": f'intitle:"{title}" inauthor:"{author}"', "maxResults": 5, "printType": "books"}
    if GOOGLE_BOOKS_KEY:
        params["key"] = GOOGLE_BOOKS_KEY
    response = client.get("https://www.googleapis.com/books/v1/volumes", params=params)
    response.raise_for_status()
    for item in response.json().get("items", []):
        links = item.get("volumeInfo", {}).get("imageLinks", {})
        url = links.get("thumbnail") or links.get("smallThumbnail")
        if url:
            return url.replace("http://", "https://").replace("&edge=curl", "")
    return None


def open_library_cover(client: httpx.Client, title: str, author: str) -> str | None:
    """Capa pela Open Library (não precisa de chave)."""
    response = client.get(
        "https://openlibrary.org/search.json",
        params={"title": title, "author": author, "limit": 5, "fields": "cover_i"},
    )
    response.raise_for_status()
    for doc in response.json().get("docs", []):
        if doc.get("cover_i"):
            return f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
    return None


def find_cover(client: httpx.Client, title: str, author: str) -> str | None:
    """Tenta o Google Books e depois a Open Library; devolve a URL da capa ou None."""
    for source, name in ((google_books_cover, "Google Books"), (open_library_cover, "Open Library")):
        try:
            url = source(client, title, author)
            if url:
                return url
        except httpx.HTTPStatusError as err:
            # mostra só o status, para não imprimir a URL com a chave
            print(f"  aviso: {name} respondeu {err.response.status_code} para {title}")
        except httpx.HTTPError as err:
            print(f"  aviso: {name} falhou para {title} ({type(err).__name__})")
    return None


def seed():
    # trava de segurança: o seed APAGA todos os livros, então só roda com DEMO_MODE=true
    if not DEMO_MODE:
        raise SystemExit(
            "Abortado: o seed apaga todos os livros e só roda no banco da demo.\n"
            "Defina DEMO_MODE=true no .env (e confira se o DATABASE_URL é o da demo)."
        )

    Base.metadata.create_all(engine)

    db = SessionLocal()
    try:
        # recomeça do zero: apaga todos os livros (exemplos antigos e de visitantes)
        db.execute(text("DELETE FROM livros"))

        if db.query(Profile).filter(Profile.id == 1).first() is None:
            db.add(Profile(id=1, photo_url=None))

        headers = {"User-Agent": "MyOwnBookShelf-demo-seed/1.0"}
        with httpx.Client(timeout=10, headers=headers, follow_redirects=True) as client:
            for example in EXAMPLES:
                cover = find_cover(client, example.get("cover_title", example["title"]), example["author"])
                db.add(
                    Book(
                        title=example["title"],
                        author=example["author"],
                        gender=example["gender"],
                        synopsis=example["synopsis"],
                        grade=example["grade"],
                        comment=example["comment"],
                        reading_status=example["reading_status"],
                        favorite=example["favorite"],
                        cover_url=cover,
                        add_date=days_ago(example["added"]),
                        finished_date=days_ago(example["finished"]) if example["finished"] is not None else None,
                        is_example=True,
                    )
                )
                print(f"{'capa ok ' if cover else 'sem capa'}  {example['title']}")

        db.commit()
        print(f"\nDemo pronta: {len(EXAMPLES)} livros de exemplo.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
