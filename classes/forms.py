from django import forms
from .models import Class, Student
from django.forms import DateInput

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'name': 'Nome',
            'description': 'Descrição',
        }

class StudentForm(forms.ModelForm):
    class_pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Student
        fields = ['name', 'email', 'student_id', 'classes', 'data_nascimento']
        widgets = {
            'email': forms.EmailInput(attrs={'required': False}),
            'student_id': forms.TextInput(attrs={'type': 'text'}),
            'data_nascimento': DateInput(
                attrs={
                    'type': 'date',
                    'placeholder': 'DD/MM/AAAA',
                    'class': 'form-control'
                }
            ),
            'classes': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nome completo',
            'email': 'E-mail (opcional)',
            'student_id': 'Número de matrícula',
            'data_nascimento': 'Data de Nascimento',
            'classes': 'Turmas',
        }

    def __init__(self, *args, **kwargs):
        # Recebe o usuário como parâmetro
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['email'].required = False

        # IMPORTANTE: Filtra as turmas apenas do usuário logado
        if user:
            self.fields['classes'].queryset = Class.objects.filter(user=user).order_by('name')
        else:
            # Se não houver usuário, não mostra nenhuma turma
            self.fields['classes'].queryset = Class.objects.none()

        # Estilizando todos os campos
        for field_name, field in self.fields.items():
            if field_name not in ['classes', 'class_pk', 'data_nascimento']:
                field.widget.attrs.update({'class': 'form-control'})

        # Adicionando placeholder específico para data de nascimento
        self.fields['data_nascimento'].widget.attrs.update({'placeholder': 'DD/MM/AAAA'})

        if 'initial' in kwargs and 'class_pk' in kwargs['initial']:
            self.fields['class_pk'].initial = kwargs['initial']['class_pk']

    def save(self, commit=True):
        student = super().save(commit=False)
        if commit:
            student.save()
            class_pk = self.cleaned_data.get('class_pk')
            if class_pk:
                try:
                    class_obj = Class.objects.get(pk=class_pk)
                    student.classes.add(class_obj)
                except Class.DoesNotExist:
                    pass
        return student

class StudentImportForm(forms.Form):
    file = forms.FileField(
        label='Arquivo (PDF ou Excel)',
        help_text='Selecione um arquivo PDF ou Excel com a lista de alunos',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    class_id = forms.ModelChoiceField(
        queryset=Class.objects.none(),
        label='Turma',
        empty_label='Selecione uma turma',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['class_id'].queryset = Class.objects.filter(user=user).order_by('name')