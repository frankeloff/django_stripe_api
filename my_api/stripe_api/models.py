from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=80, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    price = models.IntegerField(verbose_name="Цена")

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class Order(models.Model):
    session_key = models.CharField(max_length=255, verbose_name="Сессия")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Товар")
    nmb = models.PositiveIntegerField(verbose_name="Количество")
    price = models.IntegerField(verbose_name="Цена")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
