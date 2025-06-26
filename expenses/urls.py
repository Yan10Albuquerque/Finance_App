from django.urls import path
from .views import *

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    path("add-expense/", AddExpenseView.as_view(), name="add_expense"),
    path("expenses/", ExpenseListView.as_view(), name="expense_list"),
    path("edit-expense/<int:pk>/", EditExpenseView.as_view(), name="edit_expense"),
    path("delete-expense/<int:pk>/", DeleteExpenseView.as_view(), name="delete_expense"),
    
    path("add-salary/", AddSalaryView.as_view(), name="add_salary"),
    path("salaries/", SalaryListView.as_view(), name="salary_list"),
    path("edit-salary/<int:pk>/", EditSalaryView.as_view(), name="edit_salary"),

    path("fixed-expenses/", FixedExpenseListView.as_view(), name="fixed_expense_list"),
    path("add-fixed-expense/", AddFixedExpenseView.as_view(), name="add_fixed_expense"),
    path("edit-fixed-expense/<int:pk>/", EditFixedExpenseView.as_view(), name="edit_fixed_expense"),
    path("delete-fixed-expense/<int:pk>/", DeleteFixedExpenseView.as_view(), name="delete_fixed_expense"),

    path("balance/", MonthlyBalanceView.as_view(), name="monthly_balance"),
    path("", MonthlyBalanceView.as_view(), name="home"), 
]

