from django import forms
from .models import Expense, Salary, FixedExpense 
from django.utils import timezone

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["description", "total_amount", "purchase_date", "is_installment", "installments_number"]
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "description": "Descrição",
            "total_amount": "Valor Total",
            "purchase_date": "Data da Compra",
            "is_installment": "É Parcelado?",
            "installments_number": "Número de Parcelas"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["installments_number"].required = False

    def clean(self):
        cleaned_data = super().clean()
        is_installment = cleaned_data.get("is_installment")
        installments_number = cleaned_data.get("installments_number")

        if is_installment and (installments_number is None or installments_number <= 0):
            self.add_error("installments_number", "Informe um número de parcelas válido (maior que zero).")
        elif not is_installment:
            cleaned_data["installments_number"] = 1

        return cleaned_data

class SalaryForm(forms.ModelForm):
    year = forms.IntegerField(
        min_value=2000, 
        max_value=timezone.now().year + 5, 
        initial=timezone.now().year,
        label="Ano"
    )

    class Meta:
        model = Salary
        fields = ["amount", "year"]
        labels = {
            "amount": "Salário Mensal (para o ano todo)"
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_year(self):
        year = self.cleaned_data.get("year")
        if Salary.objects.filter(user=self.user, year=year).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                "Você já cadastrou um salário para este ano. Para atualizar, edite o registro existente."
            )
        return year

class FixedExpenseForm(forms.ModelForm):
    class Meta:
        model = FixedExpense
        fields = ["description", "monthly_amount", "start_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "description": "Descrição",
            "monthly_amount": "Valor Mensal Fixo",
            "start_date": "Data de Início (Primeiro Mês)"
        }
        help_texts = {
            "start_date": "Este gasto será repetido automaticamente pelos próximos 12 meses a partir desta data."
        }

