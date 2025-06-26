from django.db import models
from django.utils import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User


class Salary(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salário Mensal (para o ano todo)")
    year = models.PositiveIntegerField(verbose_name="Ano")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'year')  
        verbose_name = "Salário"
        verbose_name_plural = "Salários"

    def __str__(self):
        return f'Salário mensal de {self.amount} para o ano {self.year}'

class Expense(models.Model):
    description = models.CharField(max_length=255, verbose_name="Descrição")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")
    purchase_date = models.DateField(default=timezone.now, verbose_name="Data da Compra")
    is_installment = models.BooleanField(default=False, verbose_name="É Parcelado?")
    installments_number = models.PositiveIntegerField(null=True, blank=True, verbose_name="Número de Parcelas")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.description} - R$ {self.total_amount}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        creating_installments = self.is_installment and self.installments_number and self.installments_number > 0
        
        if not is_new:
             old_instance = Expense.objects.get(pk=self.pk)
             if old_instance.is_installment and not self.is_installment:
                 Installment.objects.filter(expense=self).delete()
             elif not old_instance.is_installment and self.is_installment:
                 is_new = True 
             elif old_instance.is_installment and self.is_installment and \
                  (old_instance.total_amount != self.total_amount or old_instance.installments_number != self.installments_number or old_instance.purchase_date != self.purchase_date):
                 Installment.objects.filter(expense=self).delete()
                 is_new = True 

        super().save(*args, **kwargs) 

        if creating_installments and is_new: 
            installment_amount = self.total_amount / Decimal(self.installments_number)
            for i in range(self.installments_number):
                due_date = self.purchase_date + relativedelta(months=i)
                Installment.objects.create(
                    expense=self,
                    installment_amount=installment_amount,
                    due_date=due_date,
                    month=due_date.month,
                    year=due_date.year,
                    user=self.user
                )

class Installment(models.Model):
    expense = models.ForeignKey(Expense, related_name='installments', on_delete=models.CASCADE)
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
        
    def __str__(self):
        return f'Parcela de {self.expense.description} - R$ {self.installment_amount} - Venc: {self.due_date.strftime("%m/%Y")}'

    class Meta:
        ordering = ['due_date']

class FixedExpense(models.Model):
    description = models.CharField(max_length=255, verbose_name="Descrição")
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Mensal Fixo")
    start_date = models.DateField(default=timezone.now, verbose_name="Data de Início (Primeiro Mês)")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.description} - R$ {self.monthly_amount}/mês (a partir de {self.start_date.strftime("%m/%Y")})'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new: 
            for i in range(12):
                occurrence_date = self.start_date + relativedelta(months=i)
                FixedExpenseOccurrence.objects.create(
                    fixed_expense=self,
                    amount=self.monthly_amount,
                    occurrence_date=occurrence_date,
                    month=occurrence_date.month,
                    year=occurrence_date.year,
                    user=self.user
                )

class FixedExpenseOccurrence(models.Model):
    fixed_expense = models.ForeignKey(FixedExpense, related_name='occurrences', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    occurrence_date = models.DateField() 
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'Ocorrência de {self.fixed_expense.description} - R$ {self.amount} - Mês: {self.occurrence_date.strftime("%m/%Y")}'

    class Meta:
        ordering = ['occurrence_date']
        verbose_name = "Ocorrência de Gasto Fixo"
        verbose_name_plural = "Ocorrências de Gastos Fixos"

