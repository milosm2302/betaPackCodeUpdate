from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils.text import slugify
import re


STORE_CHOICES = [
    ('steel', 'Gvožđara'),
    ('ambalaza', 'Ambalaža'),
]

SELLING_MODE_CHOICES = [
    ('piece', 'Po komadu'),
    ('length', 'Po metraži'),
    ('package', 'Po pakovanju'),
    ('weight', 'Po kilogramu'),
    ('on_request', 'Na upit'),
]


class Category(models.Model):
    store = models.CharField(max_length=20, choices=STORE_CHOICES, default='steel')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['store', 'name']
        unique_together = ['store', 'name']

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Subcategories'
        ordering = ['category__name', 'name']
        unique_together = ['category', 'name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Product(models.Model):
    store = models.CharField(max_length=20, choices=STORE_CHOICES, default='steel')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, blank=True, help_text="SEO-friendly URL (auto-generiše se iz naziva)")
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField(max_length=200, blank=True, help_text="Dimenzije proizvoda (npr. 500ml)")

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )

    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    on_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Dodato: Featured proizvod
    featured = models.BooleanField(default=False, help_text="Prikaži na početnoj strani")

    # Dodato: Stock (zalihe)
    in_stock = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=0, help_text="Količina na lageru (0 = neograničeno)")

    # Način prodaje
    selling_mode = models.CharField(
        max_length=20,
        choices=SELLING_MODE_CHOICES,
        default='piece',
        help_text="Način prodaje proizvoda"
    )
    package_size = models.PositiveIntegerField(
        default=1,
        help_text="Broj komada u jednom pakovanju (za prodaju po pakovanju)"
    )

    # Dodato: Prodaja po metraži (steel - legacy, koristi selling_mode='length')
    sold_by_length = models.BooleanField(default=False, help_text="Proizvod se prodaje po metraži")
    length_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=6.0,
        blank=True,
        null=False,
        help_text="Dužina 1 komada u metrima (npr. 6.0 za 6m)"
    )

    # Dodato: Custom sortiranje
    order = models.IntegerField(default=0, help_text="Redosled prikaza (manji broj = viši u listi)")
    
    def _generate_slug(self, base_slug):
        """Generiše jedinstveni slug sa Latiničnim karakterima"""
        # Transliteracija ćiriličnih karaktera u latinične
        cyrillic_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'ђ': 'dj', 'е': 'e', 'ж': 'z',
            'з': 'z', 'и': 'i', 'ј': 'j', 'к': 'k', 'л': 'l', 'љ': 'lj', 'м': 'm', 'н': 'n',
            'њ': 'nj', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'ћ': 'c', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'c', 'џ': 'dz', 'ш': 's',
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Ђ': 'Dj', 'Е': 'E', 'Ж': 'Z',
            'З': 'Z', 'И': 'I', 'Ј': 'J', 'К': 'K', 'Л': 'L', 'Љ': 'Lj', 'М': 'M', 'Н': 'N',
            'Њ': 'Nj', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'Ћ': 'C', 'У': 'U',
            'Ф': 'F', 'Х': 'H', 'Ц': 'C', 'Ч': 'C', 'Џ': 'Dz', 'Ш': 'S'
        }

        # Transliteriši ćirilicu u latinicu
        transliterated = ''.join(cyrillic_map.get(char, char) for char in base_slug)

        # Slugify transliterisani tekst
        slug = slugify(transliterated)

        # Proveri jedinstvenost slug-a
        unique_slug = slug
        num = 1
        while Product.objects.filter(slug=unique_slug, store=self.store).exclude(pk=self.pk).exists():
            unique_slug = f'{slug}-{num}'
            num += 1

        return unique_slug

    def save(self, *args, **kwargs):
        """Override save da osigura da length_per_unit uvek ima vrednost i generiše slug"""
        if self.category_id and not self.store:
            self.store = self.category.store
        elif self.category_id:
            self.store = self.category.store

        if self.sold_by_length and self.selling_mode == 'piece':
            self.selling_mode = 'length'

        if self.length_per_unit is None or self.length_per_unit == 0:
            self.length_per_unit = 6.0

        if self.selling_mode == 'on_request':
            self.price = None

        # Automatski generiši slug ako ne postoji
        if not self.slug:
            self.slug = self._generate_slug(self.name)

        super().save(*args, **kwargs)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']  # Prvo po custom order, pa po datumu
        unique_together = ['store', 'slug']

    def __str__(self):
        return self.name

    @property
    def current_price(self):
        """Trenutna cena proizvoda (akcijska ako je na akciji, inače osnovna)"""
        if self.selling_mode == 'on_request':
            return None
        if self.on_sale and self.sale_price:
            return self.sale_price
        return self.price

    @property
    def min_price(self):
        """Minimalna cena - prioritet akcijskim varijantama (za prikaz 'od' cene)"""
        if self.variants.exists():
            # Prvo pokušaj naći najnižu cenu među akcijskim varijantama
            sale_variants = self.variants.filter(on_sale=True)
            if sale_variants.exists():
                # IMA akcijske varijante - prikaži najnižu akcijsku cenu
                sale_prices = [v.current_price for v in sale_variants]
                return min(sale_prices) if sale_prices else self.current_price
            # NEMA akcijske varijante - prikaži najnižu regularnu cenu
            variant_prices = [v.current_price for v in self.variants.all()]
            return min(variant_prices) if variant_prices else self.current_price
        return self.current_price

    @property
    def original_min_price(self):
        """Originalna cena najjeftinije akcijske varijante (za prikaz precrtane cene)"""
        if self.variants.exists():
            sale_variants = self.variants.filter(on_sale=True)
            if sale_variants.exists():
                # Pronađi akcijsku varijantu sa najnižom sale_price
                cheapest_sale = min(sale_variants, key=lambda v: v.current_price)
                return cheapest_sale.price  # Vrati ORIGINALNU cenu te varijante
        return None  # Nema akcijske varijante

    @property
    def has_sale_variants(self):
        """Da li bar jedna varijanta ima akciju"""
        return self.variants.filter(on_sale=True).exists()


class ProductVariant(models.Model):
    """
    Varijante proizvoda - npr. različite dimenzije za isti proizvod
    Primer: Tačna 70 može imati više dimenzija
    Svaka varijanta ima svoju cenu i može nezavisno biti na akciji
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField(max_length=100, help_text="Npr: 180×135×18mm")

    # Cena varijante (svaka varijanta ima sopstvenu cenu)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Osnovna cena ove varijante"
    )

    # Akcija za varijantu (nezavisno od drugih varijanti)
    on_sale = models.BooleanField(default=False, help_text="Da li je varijanta na akciji")
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Akcijska cena varijante"
    )

    # Opciono: šifra/SKU za varijantu
    sku = models.CharField(max_length=50, blank=True)

    # Stock za varijantu
    in_stock = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=0)

    # Dužina 1 komada za proizvode po metraži (opciono - ako nije postavljeno, koristi se product.length_per_unit)
    length_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Dužina 1 komada u metrima za ovu varijantu (npr. 4.0 za 4m). Ako nije postavljeno, koristi se dužina iz proizvoda."
    )

    # Numerička vrednost za sortiranje (ekstraktovana iz name-a)
    dimension_value = models.IntegerField(
        default=0,
        help_text="Numerička vrednost za sortiranje (npr. 20 za '20x20', 100 za '100x100')"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['dimension_value', 'name']
        unique_together = ['product', 'name']

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def _extract_dimension_value(self):
        """Ekstraktuje numeričku vrednost iz imena varijante za sortiranje"""
        import re
        # Traži prvi broj u imenu (npr. "20x20" -> 20, "100x100" -> 100, "180×135×18mm" -> 180)
        match = re.search(r'(\d+)', self.name)
        if match:
            return int(match.group(1))
        return 0

    def save(self, *args, **kwargs):
        """Override save da automatski postavi dimension_value iz name-a"""
        if not self.dimension_value or self.dimension_value == 0:
            self.dimension_value = self._extract_dimension_value()
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        """Trenutna cena varijante (akcijska ako je na akciji, inače osnovna)"""
        if self.on_sale and self.sale_price:
            return self.sale_price
        return self.price

    @property
    def final_price(self):
        """Alias za current_price (za kompatibilnost)"""
        return self.current_price
    
    @property
    def effective_length_per_unit(self):
        """Vraća length_per_unit varijante ili proizvoda ako varijanta nema svoju"""
        if self.length_per_unit is not None:
            return self.length_per_unit
        # Fallback na product.length_per_unit
        if hasattr(self, 'product') and self.product:
            return self.product.length_per_unit if hasattr(self.product, 'length_per_unit') else 6.0
        return 6.0


def get_image_storage():
    """Get the appropriate storage backend for images"""
    from django.conf import settings

    # Direktno vraćaj instancu CloudinaryMediaStorage ako je produkcija
    if not settings.DEBUG:
        from shop.storage import CloudinaryMediaStorage
        print("[MODELS] Returning CloudinaryMediaStorage instance")
        return CloudinaryMediaStorage()
    else:
        from django.core.files.storage import default_storage
        print("[MODELS] Returning default_storage")
        return default_storage


class ProductImage(models.Model):
    """
    Slike proizvoda - više slika po proizvodu
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='products/%Y/%m/',
        storage=get_image_storage
    )
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False, help_text="Glavna slika")
    order = models.IntegerField(default=0, help_text="Redosled prikaza")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'order', 'created_at']

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"

    def save(self, *args, **kwargs):
        # Ako je ova slika primary, ostale za isti proizvod više nisu
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


# Validator za srpski broj telefona
phone_validator = RegexValidator(
    regex=r'^(\+381|0)[0-9]{8,9}$',
    message="Unesite ispravan broj telefona (npr: 0641234567 ili +381641234567)"
)


class Order(models.Model):
    """
    Narudžbine
    """
    STATUS_CHOICES = [
        ('pending', 'Na čekanju'),
        ('confirmed', 'Potvrđena'),
        ('processing', 'U obradi'),
        ('completed', 'Završena'),
        ('cancelled', 'Otkazana'),
    ]

    # Kontakt podaci kupca
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(
        max_length=20,
        validators=[phone_validator],
        help_text="Obavezan broj telefona"
    )
    customer_email = models.EmailField(blank=True, null=True, help_text="Opciono")

    # Adresa dostave (obavezno) - samo Republika Srbija
    address = models.CharField(
        max_length=200,
        help_text="Ulica i broj (obavezno)"
    )
    city = models.CharField(
        max_length=100,
        help_text="Grad (obavezno, samo Republika Srbija)"
    )

    # Prodavnica iz koje je narudžbina (steel / ambalaza)
    store = models.CharField(max_length=20, choices=STORE_CHOICES, default='steel')

    # Status i napomene
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True, help_text="Napomena kupca")
    admin_notes = models.TextField(blank=True, help_text="Interne napomene")

    # Totali
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Notifikacije poslate
    sms_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Narudžbina #{self.id} - {self.customer_name}"


class OrderItem(models.Model):
    """
    Stavke narudžbine
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        help_text="Odabrana varijanta/dimenzija"
    )

    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, help_text="Količina (može biti decimalna za proizvode po metraži)")

    # Snapshot cene u momentu narudžbine
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Snapshot naziva (ako se proizvod obriše kasnije)
    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        variant_info = f" ({self.variant_name})" if self.variant_name else ""
        return f"{self.product_name}{variant_info} x{self.quantity}"

    def save(self, *args, **kwargs):
        # Auto-calculate total_price
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    """
    Kontakt poruke sa kontakt forme
    """
    store = models.CharField(max_length=20, choices=STORE_CHOICES, default='steel', blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(
        max_length=20,
        validators=[phone_validator],
        blank=True,
        null=True
    )
    message = models.TextField()

    # Status
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Kontakt poruka'
        verbose_name_plural = 'Kontakt poruke'

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        # Bar jedno od njih mora biti popunjeno
        if not self.email and not self.phone:
            raise ValidationError('Morate navesti bar email ili telefon.')

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"


# Import scraping models
from .models_scraping import CompetitorSite, ScrapedProduct, PriceHistory, ScrapeLog
