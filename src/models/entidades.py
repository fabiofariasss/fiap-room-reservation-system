from werkzeug.security import generate_password_hash, check_password_hash

class Usuario:
    def __init__(self, nome, email, senha=None, senha_hash=None):
        self.nome = nome
        self.email = email
        if senha:
            self.senha_hash = generate_password_hash(senha)
        else:
            self.senha_hash = senha_hash

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self):
        return {
            "nome": self.nome,
            "email": self.email,
            "senha": self.senha_hash
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            nome=data.get("nome"),
            email=data.get("email"),
            senha_hash=data.get("senha")
        )

class Reserva:
    def __init__(self, sala, dia, inicio, fim, email, nome=None):
        self.sala = sala
        self.dia = dia
        self.inicio = inicio
        self.fim = fim
        self.email = email
        self.nome = nome

    def to_dict(self):
        return {
            "sala": self.sala,
            "dia": self.dia,
            "inicio": self.inicio,
            "fim": self.fim,
            "email": self.email,
            "nome": self.nome
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            sala=data.get("sala"),
            dia=data.get("dia"),
            inicio=data.get("inicio"),
            fim=data.get("fim"),
            email=data.get("email"),
            nome=data.get("nome")
        )

class Sala:
    def __init__(self, nome, capacidade=None):
        self.nome = nome
        self.capacidade = capacidade
