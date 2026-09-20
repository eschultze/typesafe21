from database import init_db
from ui.app import TypesafeApp


def main():
    init_db()
    app = TypesafeApp()
    app.run()


if __name__ == "__main__":
    main()
