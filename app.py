from flask import Flask, render_template, request
from sympy import symbols, lambdify, sin, cos, tan, exp, log, sqrt, pi
from decimal import Decimal, getcontext

app = Flask(__name__)

# Configurar precisión decimal alta (20 dígitos)
getcontext().prec = 20


def trapecio(f, a, b, n):
    a, b, n = Decimal(a), Decimal(b), int(n)
    h = (b - a) / Decimal(n)
    x = [a + h * Decimal(i) for i in range(n + 1)]
    y = [Decimal(f(float(xi))) for xi in x]
    suma = y[0] + 2 * sum(y[1:n]) + y[n]
    return h * suma / Decimal(2)


def simpson_1_3(f, a, b, n):
    if n % 2 != 0:
        raise ValueError(
            "Simpson 1/3 requiere un número par de subdivisiones.")
    a, b, n = Decimal(a), Decimal(b), int(n)
    h = (b - a) / Decimal(n)
    x = [a + h * Decimal(i) for i in range(n + 1)]
    y = [Decimal(f(float(xi))) for xi in x]
    suma = y[0] + 4 * sum(y[1:n:2]) + 2 * sum(y[2:n-1:2]) + y[n]
    return h * suma / Decimal(3)


def simpson_3_8(f, a, b, n):
    if n % 3 != 0:
        raise ValueError(
            "Simpson 3/8 requiere un número de subdivisiones múltiplo de 3.")
    a, b, n = Decimal(a), Decimal(b), int(n)
    h = (b - a) / Decimal(n)
    x = [a + h * Decimal(i) for i in range(n + 1)]
    y = [Decimal(f(float(xi))) for xi in x]
    suma = y[0] + 3 * sum(y[1:n:3]) + 3 * sum(y[2:n:3]) + \
        2 * sum(y[3:n-1:3]) + y[n]
    return (Decimal(3) * h * suma) / Decimal(8)


metodos = {
    1: trapecio,
    2: simpson_1_3,
    3: simpson_3_8
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/resolver", methods=["POST"])
def resolver():
    datos_previos = request.form.to_dict()
    try:
        funcion_raw = datos_previos['funcion'].strip()
        # Reemplazar ^ por ** para potencias estilo matemático
        funcion = funcion_raw.replace("^", "**")

        orden = datos_previos['orden']
        n = int(datos_previos['n'])

        nombres_metodos = {
            "Trapecio": 1,
            "Simpson 1/3": 2,
            "Simpson 3/8": 3
        }

        metodo_int = nombres_metodos[datos_previos['metodo_interno']]
        metodo_ext = nombres_metodos[datos_previos['metodo_externo']]

        x_min = Decimal(datos_previos['xa'])
        x_max = Decimal(datos_previos['xb'])
        y_min = Decimal(datos_previos['ya'])
        y_max = Decimal(datos_previos['yb'])

        # Validar n para métodos
        def validar_n(n, metodo):
            if metodo == 2 and n % 2 != 0:
                raise ValueError(
                    "Simpson 1/3 requiere un número par de subdivisiones.")
            if metodo == 3 and n % 3 != 0:
                raise ValueError(
                    "Simpson 3/8 requiere un número de subdivisiones múltiplo de 3.")
        validar_n(n, metodo_int)
        validar_n(n, metodo_ext)

        x, y = symbols('x y')
        contexto = {
            "x": x, "y": y, "pi": pi,
            "sin": sin, "cos": cos, "tan": tan,
            "exp": exp, "log": log, "sqrt": sqrt
        }

        try:
            expr = eval(funcion, contexto)
        except SyntaxError:
            raise ValueError(
                "Error de sintaxis en la función. Usa * para multiplicar y punto para decimales.")
        except NameError as e:
            raise ValueError(f"Nombre no válido en la función: {e}")
        except Exception as e:
            raise ValueError(f"Error al interpretar la función: {e}")

        f_xy = lambdify((x, y), expr, modules=["numpy"])

        def integrar_dydx():
            def integrando_externo(x_val):
                def f_y(y_val): return f_xy(x_val, y_val)
                return metodos[metodo_int](f_y, y_min, y_max, n)
            return metodos[metodo_ext](integrando_externo, x_min, x_max, n)

        def integrar_dxdy():
            def integrando_externo(y_val):
                def f_x(x_val): return f_xy(x_val, y_val)
                return metodos[metodo_int](f_x, x_min, x_max, n)
            return metodos[metodo_ext](integrando_externo, y_min, y_max, n)

        resultado = integrar_dydx() if orden == "dydx" else integrar_dxdy()

        resultado_str = f"{resultado:.8f}"

        return render_template("index.html", resultado=resultado_str, datos_previos=datos_previos)

    except Exception as e:
        return render_template("index.html", error=str(e), datos_previos=datos_previos)


if __name__ == '__main__':
    app.run(debug=True)
