import re
import httpx

_DIGITS = re.compile(r"\D+")

def _clean_cnpj(cnpj: str) -> str:
    c = _DIGITS.sub("", cnpj or "")
    if len(c) != 14:
        raise ValueError("CNPJ inválido: informe 14 dígitos.")
    return c

def _normalize_brasilapi(data: dict) -> dict:
    return {
        "cnpj": _DIGITS.sub("", data.get("cnpj", "")),
        "razao_social": data.get("razao_social") or "",
        "nome_fantasia": data.get("nome_fantasia") or "",
        "email": data.get("email") or "",
        "telefone": data.get("ddd_telefone_1") or "",
        "cep": data.get("cep") or "",
        "logradouro": data.get("logradouro") or "",
        "numero": data.get("numero") or "",
        "complemento": data.get("complemento") or "",
        "bairro": data.get("bairro") or "",
        "municipio": data.get("municipio") or "",
        "uf": data.get("uf") or "",
        "atividade_principal": data.get("cnae_fiscal_descricao") or "",
    }

def fetch_cnpj(cnpj: str) -> dict:
    cnpj = _clean_cnpj(cnpj)
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    with httpx.Client(timeout=10) as client:
        r = client.get(url)
        r.raise_for_status()
        return _normalize_brasilapi(r.json())
