from django import forms
from .models import CartItem
from .models import Order

class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '10'
        })
    )
    
    # Для кофе и чая добавляем выбор веса
    grams = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=[], attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        product_type = kwargs.pop('product_type', None)
        super().__init__(*args, **kwargs)
        
        # Настраиваем выбор веса в зависимости от типа продукта
        if product_type == 'coffee':
            self.fields['grams'].widget.choices = [
                (250, '250 г'), (500, '500 г'), (1000, '1000 г')
            ]
            self.fields['grams'].required = True
            self.fields['grams'].label = 'Вес'
        elif product_type == 'tea':
            self.fields['grams'].widget.choices = [
                (100, '100 г'), (500, '500 г')
            ]
            self.fields['grams'].required = True
            self.fields['grams'].label = 'Вес'
        elif product_type == 'syrup':
            # Для сиропов скрываем поле веса
            self.fields['grams'].widget = forms.HiddenInput()
            self.fields['grams'].required = False

class UpdateCartForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10',
                'style': 'width: 80px;'
            })
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваше имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Введите вашу фамилию'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+375 (12) 345-67-89'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        # Базовая валидация телефона
        if not any(char.isdigit() for char in phone):
            raise forms.ValidationError("Телефон должен содержать цифры")
        return phone