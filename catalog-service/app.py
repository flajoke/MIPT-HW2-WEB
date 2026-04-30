from catalog import create_app
from catalog.config import settings

app = create_app()

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, threaded=True)
