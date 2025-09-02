from django.db import models
from django.contrib.auth.models import User

class Representante(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20, unique=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.codigo} - {self.user.get_full_name()}"

class Cliente(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=120)
    cnpj = models.CharField(max_length=18, blank=True)
    cidade = models.CharField(max_length=80, blank=True)
    uf = models.CharField(max_length=2, blank=True)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

class Produto(models.Model):
    sku = models.CharField(max_length=30, unique=True)
    descricao = models.CharField(max_length=160)
    familia = models.CharField(max_length=60, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.sku} - {self.descricao}"

class TabelaDePreco(models.Model):
    nome = models.CharField(max_length=60, unique=True)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class Preco(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    tabela = models.ForeignKey(TabelaDePreco, on_delete=models.CASCADE)
    preco = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('produto', 'tabela')

class Pedido(models.Model):
    STATUS = [
        ('RASCUNHO','Rascunho'),
        ('ENVIADO','Enviado'),
        ('APROVADO','Aprovado'),
        ('REJEITADO','Rejeitado')
    ]
    numero = models.CharField(max_length=20, unique=True)
    representante = models.ForeignKey(Representante, on_delete=models.PROTECT)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS, default='RASCUNHO')
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {self.numero} - {self.cliente.nome}"

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    qtd = models.DecimalField(max_digits=10, decimal_places=2)
    preco_unit = models.DecimalField(max_digits=12, decimal_places=2)
    desconto = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = (self.qtd * self.preco_unit) * (1 - (self.desconto / 100))
        super().save(*args, **kwargs)

        # === JOBS & LOGS ==================================================================
import uuid
from django.db import models
from django.utils import timezone

class Job(models.Model):
    class Status(models.TextChoices):
        QUEUED  = "queued",  "Na fila"
        RUNNING = "running", "Executando"
        SUCCESS = "success", "Sucesso"
        ERROR   = "error",   "Erro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=50, db_index=True)  # ex: sankhya_demo, full_load_demo
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED, db_index=True)
    progress = models.PositiveSmallIntegerField(default=0)  # 0..100
    payload = models.JSONField(blank=True, null=True)
    result  = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} [{self.status}]"


class JobLog(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="logs")
    ts  = models.DateTimeField(default=timezone.now, db_index=True)
    level = models.CharField(max_length=10, default="INFO")  # INFO/WARN/ERROR
    message = models.TextField()

    class Meta:
        ordering = ["-ts", "-id"]

    def __str__(self):
        return f"{self.ts:%Y-%m-%d %H:%M:%S} {self.level}: {self.message[:60]}"

