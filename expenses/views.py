from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import TemplateView, ListView
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Expense, Salary, Installment, FixedExpense, FixedExpenseOccurrence
from .forms import ExpenseForm, SalaryForm, FixedExpenseForm
from decimal import Decimal
import calendar
import locale
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from dateutil.relativedelta import relativedelta 
from django.contrib.auth.mixins import LoginRequiredMixin


@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        password1 = request.POST['password_confirm']
        if password != password1:
            messages.error(request, 'As senhas não coincidem!')
            return render(request, 'expenses/signup.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Usuário já existe!')
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('home')
    return render(request, 'expenses/signup.html')

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session.set_expiry(60 * 60 * 24 * 30)
            return redirect('home')
        else:
           messages.error(request, 'Usuário ou senha inválidos.')
    return render(request, 'expenses/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'expenses/profile.html'
    model = User
    fields = ['username', 'first_name', 'last_name', 'email']
    success_url = reverse_lazy('profile')
    
    def get_object(self, queryset=None):
        return self.request.user
        

class AddExpenseView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/add_expense.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
        
    def get_success_url(self):
        purchase_date = self.object.purchase_date
        return reverse('monthly_balance') + f'?month={purchase_date.month}&year={purchase_date.year}'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Adicionar Despesa Variável'
        return context

class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'expenses/add_or_edit_expense.html'
    context_object_name = 'expenses'
    ordering = ['-purchase_date']
    
    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user).order_by('-purchase_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Despesas Variáveis Registradas'
        context['expenses'] = self.get_queryset() 
        return context
    
class EditExpenseView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/add_expense.html'
    
    def get_success_url(self):
        purchase_date = self.object.purchase_date
        return reverse('monthly_balance') + f'?month={purchase_date.month}&year={purchase_date.year}'

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user).order_by('-purchase_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Despesa: {self.object.description}'
        return context
    
class DeleteExpenseView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'expenses/confirm_delete_expense.html'
    success_url = reverse_lazy('expense_list')
    context_object_name = 'expense'
    
    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user).order_by('-purchase_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Confirmar Exclusão: {self.object.description}'
        return context
        

class AddSalaryView(LoginRequiredMixin, CreateView):
    model = Salary
    form_class = SalaryForm
    template_name = 'expenses/add_or_edit_salary.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user 
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        year = self.object.year
        current_month = timezone.now().month
        return reverse('monthly_balance') + f'?month={current_month}&year={year}'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Adicionar Salário Anual'
        target_year = self.request.GET.get('year', timezone.now().year)
        try:
            context['existing_salary'] = Salary.objects.get(user=self.request.user, year=target_year)
        except Salary.DoesNotExist:
            context['existing_salary'] = None
        return context

class SalaryListView(LoginRequiredMixin, ListView):
    model = Salary
    template_name = 'expenses/salary_list.html'
    context_object_name = 'salaries'
    ordering = ['-year']
    
    def get_queryset(self):
        return Salary.objects.filter(user=self.request.user).order_by('-year')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Salários Anuais Registrados'
        context['salaries'] = self.get_queryset()  
        return context

class EditSalaryView(LoginRequiredMixin, UpdateView):
    model = Salary
    form_class = SalaryForm
    template_name = 'expenses/add_or_edit_salary.html'
    def get_success_url(self):
        year = self.object.year
        current_month = timezone.now().month
        return reverse('monthly_balance') + f'?month={current_month}&year={year}'

    def get_queryset(self):
        return Salary.objects.filter(user=self.request.user).order_by('-year')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Salário para {self.object.year}'
        return context

class AddFixedExpenseView(LoginRequiredMixin, CreateView):
    model = FixedExpense
    form_class = FixedExpenseForm
    template_name = 'expenses/add_or_edit_fixed_expense.html'
    success_url = reverse_lazy('fixed_expense_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
         
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Adicionar Gasto Fixo Mensal (por 12 meses)'
        return context

class FixedExpenseListView(LoginRequiredMixin, ListView):
    model = FixedExpense
    template_name = 'expenses/fixed_expense_list.html'
    context_object_name = 'fixed_expenses'
    ordering = ['-start_date']
    
    
    def get_queryset(self):
        return FixedExpense.objects.filter(user=self.request.user).order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Gastos Fixos Mensais Registrados'
        expenses_with_end_date = []
        for expense in context['fixed_expenses']:
            end_date = expense.start_date + relativedelta(months=11)
            expenses_with_end_date.append({'expense': expense, 'end_date': end_date})
        context['expenses_with_end_date'] = expenses_with_end_date
        return context

class EditFixedExpenseView(LoginRequiredMixin, UpdateView):
    model = FixedExpense
    form_class = FixedExpenseForm
    template_name = 'expenses/add_or_edit_fixed_expense.html'
    success_url = reverse_lazy('fixed_expense_list')
    
    def get_queryset(self):
        return FixedExpense.objects.filter(user=self.request.user).order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Gasto Fixo: {self.object.description}'
        return context

class DeleteFixedExpenseView(LoginRequiredMixin, DeleteView):
    model = FixedExpense
    template_name = 'expenses/confirm_delete_fixed_expense.html'
    success_url = reverse_lazy('fixed_expense_list')
    context_object_name = 'fixed_expense'
    
    def get_queryset(self):
        return FixedExpense.objects.filter(user=self.request.user).order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Confirmar Exclusão: {self.object.description}'
        return context

class MonthlyBalanceView(LoginRequiredMixin, TemplateView):
    template_name = 'expenses/monthly_balance.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login') 
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        current_month = self.request.GET.get('month', today.month)
        current_year = self.request.GET.get('year', today.year)

        try:
            current_month = int(current_month)
            current_year = int(current_year)
            if not 1 <= current_month <= 12:
                current_month = today.month
        except (ValueError, TypeError):
            current_month = today.month
            current_year = today.year

        try:
            salary_obj = Salary.objects.get(user=self.request.user, year=current_year)
            salary_amount = salary_obj.amount
        except Salary.DoesNotExist:
            salary_amount = Decimal('0.00')

        

        expenses_this_month = Expense.objects.filter(
            user=self.request.user,
            is_installment=False,
            purchase_date__month=current_month,
            purchase_date__year=current_year
        ).values('description', 'total_amount', 'purchase_date')
        total_expenses_direct = expenses_this_month.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

        installments_this_month = Installment.objects.filter(
            user=self.request.user,
            month=current_month, 
            year=current_year
        )
        sum_installments = installments_this_month.aggregate(total=Sum('installment_amount'))['total'] or Decimal('0.00')


        total_installments = total_expenses_direct + sum_installments
        
        fixed_expenses_this_month = FixedExpenseOccurrence.objects.filter(
            user=self.request.user,
            month=current_month,
            year=current_year
        )
        total_fixed_expenses = fixed_expenses_this_month.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        total_expenses = total_installments + total_fixed_expenses
        balance = salary_amount - total_expenses

        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
        try:
            month_name = calendar.month_name[current_month].capitalize()
        except IndexError:
            month_name = "Mês Inválido"
    
        context['title'] = f'Saldo Mensal - {month_name}/{current_year}'
        context['current_month'] = current_month
        context['current_year'] = current_year
        context['salary'] = salary_amount
        context['total_installments'] = total_installments
        context['total_fixed_expenses'] = total_fixed_expenses
        context['total_expenses'] = total_expenses
        context['balance'] = balance 
        context['installments'] = installments_this_month
        context['fixed_expenses_occurrences'] = fixed_expenses_this_month
        context['month_name'] = month_name

        context['months'] = list(range(1, 13))
        context['years'] = list(range(today.year - 5, today.year + 6))
        
        context['usuario'] = self.request.user.username
        
        
        

        return context


