from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, TimeField, IntegerField, DecimalField, BooleanField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, EqualTo
from datetime import date

class LoginForm(FlaskForm):
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])

class UserForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    user_type = SelectField('Tipo de Usuário', choices=[
        ('admin', 'Administrador'),
        ('secretary', 'Secretária'),
        ('teacher', 'Professor'),
        ('student', 'Aluno')
    ], validators=[DataRequired()])
    full_name = StringField('Nome Completo', validators=[DataRequired(), Length(max=200)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=20)])

class StudentForm(FlaskForm):
    # User fields
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[Optional(), Length(min=6)])
    full_name = StringField('Nome Completo', validators=[DataRequired(), Length(max=200)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=20)])

    # Student specific fields
    birth_date = DateField('Data de Nascimento', validators=[Optional()])
    address = TextAreaField('Endereço', validators=[Optional()])
    emergency_contact = StringField('Contato de Emergência', validators=[Optional(), Length(max=100)])
    emergency_phone = StringField('Telefone de Emergência', validators=[Optional(), Length(max=20)])
    guardian_name = StringField('Nome do Responsável', validators=[Optional(), Length(max=200)])
    guardian_phone = StringField('Telefone do Responsável', validators=[Optional(), Length(max=20)])
    guardian_email = EmailField('E-mail do Responsável', validators=[Optional(), Email()])
    medical_info = TextAreaField('Informações Médicas', validators=[Optional()])
    notes = TextAreaField('Observações', validators=[Optional()])

class TeacherForm(FlaskForm):
    # User fields
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[Optional(), Length(min=6)])
    full_name = StringField('Nome Completo', validators=[DataRequired(), Length(max=200)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=20)])

    # Teacher specific fields
    specialization = StringField('Especialização', validators=[Optional(), Length(max=200)])
    hourly_rate = DecimalField('Valor por Hora', validators=[Optional(), NumberRange(min=0)])
    bank_name = StringField('Banco', validators=[Optional(), Length(max=100)])
    bank_agency = StringField('Agência', validators=[Optional(), Length(max=20)])
    bank_account = StringField('Conta', validators=[Optional(), Length(max=20)])
    pix_key = StringField('Chave PIX', validators=[Optional(), Length(max=100)])
    bio = TextAreaField('Biografia', validators=[Optional()])
    qualifications = TextAreaField('Qualificações', validators=[Optional()])

class RoomForm(FlaskForm):
    name = StringField('Nome da Sala', validators=[DataRequired(), Length(max=100)])
    capacity = IntegerField('Capacidade', validators=[DataRequired(), NumberRange(min=1)])
    equipment = TextAreaField('Equipamentos', validators=[Optional()])
    location = StringField('Localização', validators=[Optional(), Length(max=200)])
    is_available = BooleanField('Disponível')
    notes = TextAreaField('Observações', validators=[Optional()])

class CourseForm(FlaskForm):
    name = StringField('Nome do Curso', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Descrição', validators=[Optional()])
    instrument = StringField('Instrumento', validators=[Optional(), Length(max=100)])
    level = SelectField('Nível', choices=[
        ('beginner', 'Iniciante'),
        ('intermediate', 'Intermediário'),
        ('advanced', 'Avançado')
    ], validators=[Optional()])
    duration_months = IntegerField('Duração (meses)', validators=[Optional(), NumberRange(min=1)])
    monthly_price = DecimalField('Mensalidade', validators=[DataRequired(), NumberRange(min=0)])
    max_students = IntegerField('Máximo de Alunos', validators=[DataRequired(), NumberRange(min=1)])
    teacher_id = SelectField('Professor', coerce=int, validators=[Optional()])
    is_active = BooleanField('Ativo', default=True)

class EnrollmentForm(FlaskForm):
    student_id = SelectField('Aluno', coerce=int, validators=[DataRequired()])
    course_id = SelectField('Curso', coerce=int, validators=[DataRequired()])
    discount_percentage = DecimalField('Desconto (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    notes = TextAreaField('Observações', validators=[Optional()])

class ScheduleForm(FlaskForm):
    course_id = SelectField('Curso', coerce=int, validators=[DataRequired()])
    teacher_id = SelectField('Professor', coerce=int, validators=[DataRequired()])
    room_id = SelectField('Sala', coerce=int, validators=[DataRequired()])
    day_of_week = SelectField('Dia da Semana', choices=[
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo')
    ], coerce=int, validators=[DataRequired()])
    start_time = TimeField('Horário de Início', validators=[DataRequired()])
    end_time = TimeField('Horário de Término', validators=[DataRequired()])

class PaymentForm(FlaskForm):
    student_id = SelectField('Aluno', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Valor', validators=[DataRequired(), NumberRange(min=0)])
    due_date = DateField('Data de Vencimento', validators=[DataRequired()])
    payment_date = DateField('Data de Pagamento', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('overdue', 'Vencido'),
        ('cancelled', 'Cancelado')
    ], validators=[DataRequired()])
    payment_method = StringField('Método de Pagamento', validators=[Optional(), Length(max=50)])
    reference_month = DateField('Mês de Referência', validators=[DataRequired()])
    notes = TextAreaField('Observações', validators=[Optional()])

class MaterialForm(FlaskForm):
    course_id = SelectField('Curso', coerce=int, validators=[DataRequired()])
    title = StringField('Título', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Descrição', validators=[Optional()])
    file = FileField('Arquivo', validators=[
        FileAllowed(['pdf', 'mp3', 'mp4', 'doc', 'docx', 'txt'], 'Apenas arquivos PDF, MP3, MP4, DOC, DOCX e TXT são permitidos!')
    ])
    is_public = BooleanField('Público')

class ExperimentalClassForm(FlaskForm):
    name = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=200)])
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    phone = StringField('Telefone', validators=[DataRequired()])
    age = IntegerField('Idade', validators=[DataRequired()])
    instrument = SelectField('Instrumento de Interesse', choices=[
        ('piano', 'Piano'),
        ('violao', 'Violão'),
        ('guitarra', 'Guitarra'),
        ('baixo', 'Baixo'),
        ('bateria', 'Bateria'),
        ('flauta', 'Flauta'),
        ('saxofone', 'Saxofone'),
        ('violino', 'Violino'),
        ('canto', 'Canto')
    ], validators=[DataRequired()])
    experience_level = SelectField('Nível de Experiência', choices=[
        ('beginner', 'Iniciante'),
        ('intermediate', 'Intermediário'),
        ('advanced', 'Avançado')
    ], validators=[DataRequired()])
    preferred_date = DateField('Data Preferencial', validators=[Optional()])
    preferred_time = StringField('Horário Preferencial', validators=[Optional()])
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Agendar Aula Experimental')

class EditProfileForm(FlaskForm):
    full_name = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=200)])
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    phone = StringField('Telefone', validators=[Length(max=20)])
    password = PasswordField('Nova Senha (deixe em branco para manter atual)')
    password_confirm = PasswordField('Confirmar Nova Senha', validators=[
        EqualTo('password', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Atualizar Perfil')

class ContactForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=200)])
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    phone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    subject = StringField('Assunto', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Mensagem', validators=[DataRequired()])

class NewsForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(min=5, max=200)])
    summary = TextAreaField('Resumo', validators=[Optional(), Length(max=300)])
    content = TextAreaField('Conteúdo', validators=[DataRequired()])
    category = SelectField('Categoria', choices=[
        ('announcement', 'Aviso'),
        ('event', 'Evento'),
        ('news', 'Notícia')
    ], validators=[DataRequired()])
    featured = BooleanField('Destacar na página inicial')
    is_public = BooleanField('Visível para o público')
    publish_date = DateField('Data de publicação', validators=[DataRequired()])
    submit = SubmitField('Salvar Notícia')