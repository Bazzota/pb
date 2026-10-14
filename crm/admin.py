from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from . import models 
# Register your models here.
class PhoneInline(admin.TabularInline):
	model = models.Phone
	extra = 0
	fields = ['number', 'number_owner']


class EmailInline(admin.TabularInline):
	model = models.Email
	extra = 0
	fields = ['email', 'description']


class AddressInline(admin.TabularInline):
	model = models.Address
	extra = 0
	fields = ['address_name', 'description', 'is_main', 'work_type', 'foreman']
	
	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.filter(is_main=True)


class AdditionalContractInline(admin.TabularInline):
	model = models.AdditionalContract
	extra = 0
	fields = ['number', 'address', 'start_date', 'finish_date']


class AdditionalContractItemInline(admin.TabularInline):
	model = models.AdditionalContractItem
	extra = 0
	fields = ['address', 'work_type', 'description']
	autocomplete_fields = ['address', 'work_type']	


@admin.register(models.Contract)
class ContractAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'customer', 'addresses_list', 'colored_status']
	inlines = [AddressInline]
	#list_editable = ['status']
	autocomplete_fields = ['customer',]
	search_fields = ['full_number',]
	list_filter = ['contract_type', 'year', 'month']
	
	@admin.display(description='Статус договора', ordering='status')
	def colored_status(self, obj):
	    colors = {
	        models.Contract.ContractStatus.ACTIVE: ('#1a7f37', '#d1f0d1'),
	        models.Contract.ContractStatus.DEACTIVE: ('#a40000', '#f7d5d5'),
	    }
	    fg, bg = colors.get(obj.status, ('#333', '#eee'))
	    return format_html(
	        '<span style="'
	        'display: inline-block;'
	        'padding: 2px 8px;'
	        'border-radius: 10px;'
	        'font-weight: 600;'
	        'font-size: 12px;'
	        'color: {};'
	        'background: {};'
	        '">{}</span',
	        fg, bg, obj.get_status_display(),
	        )

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.select_related('customer').prefetch_related('address_set')

	def addresses_list(self, obj):
		addresses = obj.address_set.all()
		if not addresses:
			return '-'
		
		addresses_list = []
		for address in addresses:
			if address.is_main == True:
				url = reverse('admin:crm_address_change', args=[address.id])
				link = format_html('<a href="{}">{}</a>', url, str(address))
				addresses_list.append(link)
		
		return format_html('<br>'.join(addresses_list))
	addresses_list.short_description = 'Адреса в договоре:'	


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'get_contract_list', 'get_additional_contracts_list', 'get_actual_addresses']
	inlines = [PhoneInline, EmailInline]
	search_fields = ['name']

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.prefetch_related('contract_set', 'additionalcontract_set')
	
	def get_contract_list(self, obj):
		contracts = obj.contract_set.all()
		if not contracts:
			return '-'
		contract_links = []
		for contract in contracts:
			url = reverse('admin:crm_contract_change', args=[contract.id])
			link = format_html('<a href="{}">{}</a>', url, str(contract))
			contract_links.append(link)
	
		return format_html('<br>'.join(contract_links))
	get_contract_list.short_description = 'Связанные договоры'
	
	def get_additional_contracts_list(self, obj):
		additional_contracts = obj.additionalcontract_set.all()
		if not additional_contracts:
			return '-'
		additional_contracts_list = []
		for add_contract in additional_contracts:
			url = reverse('admin:crm_additionalcontract_change', args=[add_contract.id])
			link = format_html('<a href="{}">{}</a>', url, str(add_contract))
			additional_contracts_list.append(link)
		
		return format_html('<br>'.join(additional_contracts_list))
	get_additional_contracts_list.short_description = 'Связанные Доп. соглашения'

	def get_actual_addresses(self, obj):
		result = {}
		for contract in obj.contract_set.all():
			for address in contract.address_set.all():
			    if address.address_name not in result.values():
				    result[address.id] = address.address_name

		for additional_contract in obj.additionalcontract_set.all():
			items = additional_contract.additionalcontractitem_set.all().order_by('id')
			for item in items:
				first_work_type = item.work_type.first()
				if not first_work_type:
					continue
				if first_work_type.title == 'Новый адрес':
					result[item.address.id] = item.address.address_name
				elif first_work_type.title == 'Убрать адрес':
					result.pop(item.address.id, None)
		return format_html('<br>'.join(list(result.values())))
	get_actual_addresses.short_description = 'Все актуальные адреса'

@admin.register(models.Phone)
class PhoneAdmin(admin.ModelAdmin):
	list_display = ['__str__']
	autocomplete_fields = ['customer']


@admin.register(models.Email)
class EmailAdmin(admin.ModelAdmin):
	list_display = ['__str__']	


@admin.register(models.Address)
class AddressAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'get_customer', 'foreman', 'get_related_contracts']
	search_fields = ['address_name', 'basic_contract__customer__name']
	list_filter = ['foreman']
	exclude = ['is_main']

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.select_related(
			'basic_contract__customer', 'foreman'
			).prefetch_related(
				'additional_items__additional_contract__customer'
			)

	def get_customer(self, obj):
		if obj.basic_contract:
			return obj.basic_contract.customer

		related_item = obj.additional_items.all()
		if related_item.exists():
			return related_item[0].additional_contract.customer
	get_customer.short_description = 'На ТО:'

	def get_related_contracts(self, obj):
		all_related_contracts = []
		if obj.basic_contract:
			url = reverse('admin:crm_contract_change', args=[obj.basic_contract.id])
			link = format_html('<a href="{}">{}</a>', url, str(obj.basic_contract))
			all_related_contracts.append(link)
		for item in obj.additional_items.all():
			url = reverse('admin:crm_additionalcontract_change', args=[item.additional_contract.id])
			link = format_html('<a href="{}">{}</a>', url, str(item.additional_contract))
			all_related_contracts.append(link)
		return format_html('<br>'.join(all_related_contracts))
	get_related_contracts.short_description = 'Связанные договоры:'


@admin.register(models.WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
	list_display = ['__str__']
	search_fields = ['title']


@admin.register(models.Foreman)
class ForemanAdmin(admin.ModelAdmin):
	list_display = ['__str__']


@admin.register(models.AdditionalContract)
class AdditionalContractAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'customer','get_addresses_list', 'start_date'] 
	inlines = [AdditionalContractItemInline]
	search_fields = ['customer__name']
	autocomplete_fields = ['basic_contract', 'customer']

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.select_related(
			'customer'
		).prefetch_related(
			'additionalcontractitem_set__address'
		)
	
	def get_addresses_list(self, obj):
		additional_contract_items = obj.additionalcontractitem_set.all()
		if not additional_contract_items:
			return '-'
		addresses_line = [ str(item.address) for item in additional_contract_items ]
		return format_html('<br>'.join(addresses_line))
	get_addresses_list.short_description = 'Адреса в договоре'	


@admin.register(models.AdditionalContractItem)
class AdditionalContractItemAdmin(admin.ModelAdmin):
	list_display = ['__str__']
	autocomplete_fields = ['address']
# Register your models here.
