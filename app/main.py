from flask import Flask
from app.models import db, Producto

app = Flask(__name__)

app.config["SECRET_KEY"] = "contraseña"

# Configuración de la base de datos (En local = SQLite)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tienda.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Vinculamos SQLAlchemy con nuestra aplicación de Flask
db.init_app(app)

with app.app_context():
    db.create_all()  # Crea las tablas en la base de datos (si no existieran)

    if not Producto.query.first():
        nuevo_producto = Producto(
            nombre="Teclado Mecánico RGB",
            precio=49.99,
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        print(">>>>> Producto de prueba insertado en la BD <<<<<<<<<")


@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/test.db")
def test_db():
    productos = Producto.query.all()
    return f"Todos los productos: {productos}"


if __name__ == "__main__":
    app.run(debug=True)
