from django import forms
from .models import Class, Student

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
        fields = ['name', 'email', 'student_id']
        widgets = {
            'email': forms.EmailInput(attrs={'required': False}),
            'student_id': forms.TextInput(attrs={'type': 'text'})  # <- Aqui está o ajuste
        }
        labels = {
            'name': 'Nome completo',
            'email': 'E-mail (opcional)',
            'student_id': 'Número de matrícula',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
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
        help_text='Selecione um arquivo PDF ou Excel com a lista de alunos'
    )
    class_id = forms.ModelChoiceField(
        queryset=Class.objects.none(),
        label='Turma',
        empty_label='Selecione uma turma'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['class_id'].queryset = Class.objects.filter(user=user)