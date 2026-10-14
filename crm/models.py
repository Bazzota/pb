from django.db import models

# Create your models here.
class Contract(models.Model):
	class OurCompany(models.TextChoices):
		ENTREPRENEUR = 'IP', 'ИП'
		LLC = 'OOO', 'ПБ'

	class ContractType(models.TextChoices):
		SERVICE = 'TO', 'ТО'
		INSTALLATION = 'M', 'М'

	class Month(models.IntegerChoices):
		JAN = 1, '01',
		FEB = 2, '02',
		MAR = 3, '03',
		APR = 4, '04',
		MAY = 5, '05',
		JUN = 6, '06',
		JUL = 7, '07',
		AUG = 8, '08',
		SEP = 9, '09',
		OCT = 10, '10',
		NOV = 11, '11',
		DEC = 12, '12',

	class DocumentFlow(models.TextChoices):
		EDM = 'EDM', 'ЭДО'
		PAPER = 'Paper', 'Бумага'
		NOTHING = 'Nothing', 'Неопределен'

	class ContractStatus(models.TextChoices):
		ACTIVE = 'ON', 'Рабочий'
		DEACTIVE = 'OFF', 'Нерабочий' 		

	company_type = models.CharField(max_length=5, choices=OurCompany.choices, verbose_name='Фирма')
	contract_type = models.CharField(max_length=5, choices=ContractType.choices, verbose_name='Тип договора')
	year = models.IntegerField(verbose_name='Год', null=True, blank=True)
	month = models.IntegerField(choices=Month.choices, null=True, blank=True, verbose_name='Месяц')
	number = models.IntegerField(null=True, blank=True, verbose_name='Номер')
	legacy_number = models.CharField(max_length=30, blank=True, null=True, verbose_name='Старый номер договора', help_text='Для договоров со старой нумерацией')
	customer = models.ForeignKey(to='Customer', on_delete=models.PROTECT, verbose_name='Контрагент', null=True)
	date = models.DateField(verbose_name='Дата договора')
	finish_date = models.DateField(verbose_name='Дата оканчания договора', blank=True, null=True)
	price = models.DecimalField(decimal_places=2, max_digits=9, null=True, verbose_name='Стоимость договора')
	documents = models.CharField(max_length=10, choices=DocumentFlow.choices, verbose_name='Документооборот')
	status = models.CharField(max_length=10, choices=ContractStatus.choices, verbose_name='Статус договора', default=ContractStatus.ACTIVE)
	full_number = models.CharField(max_length=30, blank=True, editable=False, null=True)

	class Meta:
		verbose_name = 'Договор'
		verbose_name_plural = 'Договоры'
		ordering = ['-year', '-month', '-number']
		constraints = [
			models.UniqueConstraint(
				fields= ['company_type', 'contract_type', 'year', 'month', 'number'],
				name='unique_contract_identication',
				condition=models.Q(legacy_number__isnull=True)
			)
		]

	def save(self, *args, **kwargs):
		if self.legacy_number:
			self.full_number = self.legacy_number
		else:
			company_display = dict(self.OurCompany.choices).get(self.company_type, self.company_type)
			contract_display = dict(self.ContractType.choices).get(self.contract_type, self.contract_type)
			year_display = str(self.year)
			month_display = str(self.month)
			number_display = str(self.number)
			self.full_number = f'{company_display}-{contract_display}-{year_display}-{month_display}-{number_display}'	
		return super().save(*args, **kwargs)	

	def __str__(self):
		if self.legacy_number:
			return self.legacy_number

		#return self.full_number
		return f'{self.get_company_type_display()}-{self.get_contract_type_display()}-{self.year}-{self.get_month_display()}-{self.number}'
	

class Customer(models.Model):
	name = models.CharField(max_length=150, unique=True, verbose_name='Название')
	inn = models.CharField(max_length=20, unique=True, verbose_name='ИНН')

	class Meta:
		verbose_name = 'Контрагент'
		verbose_name_plural = 'Контрагенты'

	def __str__(self):
		return self.name


class Phone(models.Model):
	number = models.CharField(max_length=30, verbose_name='Номер телефона', blank=True)
	number_owner = models.CharField(max_length=60, verbose_name='Владелец номера', blank=True)
	customer = models.ForeignKey(to='Customer', on_delete=models.CASCADE, verbose_name='Контрагент', null=True, blank=True)

	class Meta:
		verbose_name = 'Номер телефона'
		verbose_name_plural = 'Номера телефонов'

	def __str__(self):
		return self.number


class Email(models.Model):
	email = models.EmailField(verbose_name='Email', blank=True)
	description = models.CharField(max_length=100, verbose_name='Описание', blank=True)
	customer = models.ForeignKey(to='Customer', on_delete=models.CASCADE, verbose_name='Контрагент', null=True, blank=True)

	class Meta:
		verbose_name = 'Email'
		verbose_name_plural = 'Emails'

	def __str__(self):
		return self.email


class Address(models.Model):
	address_name = models.CharField(max_length=150, verbose_name='Адрес')
	description = models.TextField(verbose_name='Доп. описание', blank=True)
	basic_contract = models.ForeignKey(to='Contract', on_delete=models.SET_NULL, null=True, blank=True, editable=False, verbose_name='Основной договор')
	work_type = models.ManyToManyField(to='WorkType', blank=True, verbose_name='Виды работ')
	foreman = models.ForeignKey(to='Foreman', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Техник')
	is_main = models.BooleanField(default=False, verbose_name='Адрес из основного договора?')

	class Meta:
		verbose_name = 'Адрес'
		verbose_name_plural = 'Адреса'

	def __str__(self):
		
		return self.address_name 


class WorkType(models.Model):
	title = models.CharField(max_length=50, unique=True, verbose_name='Название')

	class Meta:
		verbose_name = 'Вид работы'
		verbose_name_plural = 'Виды работ'

	def __str__(self):
		return self.title	
		

class Foreman(models.Model):
	name = models.CharField(max_length=15, verbose_name='Имя')
	surname = models.CharField(max_length=15, verbose_name='Фамилия')

	class Meta:
		verbose_name = 'Техник'
		verbose_name_plural = 'Техники'

	def __str__(self):
		return f'{self.surname} {self.name}'


class AdditionalContract(models.Model):
	customer = models.ForeignKey(to='Customer', on_delete=models.CASCADE, verbose_name='Контрагент')
	basic_contract = models.ForeignKey(to='Contract', on_delete=models.CASCADE, verbose_name='Основной договор')
	number = models.IntegerField(verbose_name='Номер')
	start_date = models.DateField(verbose_name='Старт контракта')
	finish_date = models.DateField(verbose_name='Окончание работ', null=True, blank=True)
	price = models.DecimalField(verbose_name='Цена', blank=True, null=True, decimal_places=2, max_digits=12)

	class Meta:
		verbose_name = 'Доп. соглашение'
		verbose_name_plural = 'Доп. соглашения'
		ordering = ['-start_date', 'number']
		constraints = [
			models.UniqueConstraint(
				fields= ['basic_contract', 'number'],
				name = 'unique_addcontract_identificator'
			)
		]

	def __str__(self):
		return f'ДС №{self.number} к {self.basic_contract}'


class AdditionalContractItem(models.Model):
	additional_contract = models.ForeignKey(to='AdditionalContract', on_delete=models.PROTECT, verbose_name='Доп. контракт')
	address = models.ForeignKey(to='Address',
		on_delete=models.PROTECT,
		related_name='additional_items',
		verbose_name='Адрес. При добавление нового адреса, для всех работ, кроме "Увеличение объемов", впишите ТОЛЬКО адрес.')
	work_type = models.ManyToManyField(to='WorkType', verbose_name='Вид работы')
	description = models.TextField(blank=True, verbose_name='Описание')

	class Meta:
		verbose_name = 'Объект доп. контракта'
		verbose_name_plural = 'Объекты доп. контракта'
