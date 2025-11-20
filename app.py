from app import create_app
from app.config.config import DEBUG


# WSGI için kullanılacak uygulama nesnesi
app = create_app()


if __name__ == "__main__":
    # Geliştirme ortamında çalıştırmak için:
    # python app.py
    app.run(
        debug=DEBUG,
        host="0.0.0.0",
        port=5000,
        threaded=True,
    )


