from rest_framework import serializers
from .models import Category, Subcategory, Product, ProductVariant, ProductImage, Order, OrderItem, ContactMessage


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'description', 'category', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'store', 'name', 'description', 'subcategories', 'product_count', 'created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    # Koristimo SerializerMethodField za read, ali dozvoljavamo write preko image field-a
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        # Vrati URL slike - može biti Cloudinary ili lokalni /media/
        if obj.image and obj.image.name:
            try:
                url = obj.image.url
                # Ako je URL potpuna adresa (http/https), vrati ga direktno (Cloudinary)
                if url.startswith('http://') or url.startswith('https://'):
                    return url
                # Inače je lokalni URL, vrati ga direktno
                return url
            except (ValueError, AttributeError):
                return None
        return None
    
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'image_url', 'alt_text', 'is_primary', 'order', 'created_at']
        extra_kwargs = {
            'image': {'write_only': True}  # image je samo za write
        }
    
    def to_representation(self, instance):
        # Override to_representation da vratimo image_url kao image
        ret = super().to_representation(instance)
        # Zameni image_url sa image za kompatibilnost sa frontend-om
        if 'image_url' in ret:
            ret['image'] = ret.pop('image_url')
        return ret


class ProductVariantSerializer(serializers.ModelSerializer):
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    effective_length_per_unit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'name', 'price', 'on_sale', 'sale_price',
            'current_price', 'final_price', 'sku',
            'in_stock', 'stock_quantity', 'length_per_unit', 'effective_length_per_unit',
            'created_at'
        ]
        extra_kwargs = {
            'length_per_unit': {'required': False, 'allow_null': True}
        }


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    original_min_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    has_sale_variants = serializers.BooleanField(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'store', 'name', 'slug', 'description', 'price', 'dimensions',
            'on_sale', 'sale_price',
            'category', 'category_name', 'subcategory', 'subcategory_name',
            'current_price', 'min_price', 'original_min_price', 'has_sale_variants',
            'featured', 'in_stock', 'stock_quantity',
            'selling_mode', 'package_size',
            'sold_by_length', 'length_per_unit',
            'order', 'variants', 'images', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'length_per_unit': {'required': False},
            'slug': {'read_only': True},
            'price': {'required': False, 'allow_null': True},
        }
        # Slug se auto-generiše u modelu; ne validiramo unique_together(store, slug) na nivou serializera
        validators = []

    def to_internal_value(self, data):
        """
        Podržava store-lokalne ID-jeve kategorija za Ambalažu.

        Primer: ako payload pošalje store="ambalaza" i category=2, a globalna
        kategorija #2 pripada gvožđari, category=2 se tumači kao druga
        ambalaža kategorija (po ID redosledu) i prevodi se na njen pravi DB ID.

        Ako je poslati category već pravi globalni ID za dati store, ne menjamo ga.
        Steel tok ostaje kompatibilan sa postojećim ponašanjem.
        """
        mutable_data = data.copy()
        store = mutable_data.get('store')
        category_value = mutable_data.get('category')

        if store and category_value not in (None, ''):
            try:
                category_number = int(category_value)
            except (TypeError, ValueError):
                category_number = None

            if category_number is not None:
                category = Category.objects.filter(pk=category_number).first()
                if category is None or category.store != store:
                    if category_number < 1:
                        raise serializers.ValidationError({
                            'category': ['ID kategorije mora biti veći od 0.']
                        })

                    local_category = Category.objects.filter(store=store).order_by('id')[
                        category_number - 1:category_number
                    ].first()

                    if not local_category:
                        raise serializers.ValidationError({
                            'category': [f'Kategorija {category_number} ne postoji za prodavnicu {store}.']
                        })

                    mutable_data['category'] = local_category.id

        return super().to_internal_value(mutable_data)
    
    def validate_length_per_unit(self, value):
        """Validacija za length_per_unit"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Dužina mora biti veća od 0")
        return value

    def validate(self, data):
        """
        Cena sme biti prazna SAMO za ambalažu sa načinom prodaje "na upit" (on_request).
        Ako store nije naglašen u API-ju → tretira se kao steel (gvožđara) i cena je OBAVEZNA.
        Time se za gvožđaru zadržava originalno ponašanje (cena obavezna).
        """
        # Kategorija je source of truth za prodavnicu (model radi isto pri save-u).
        # Ako store nije naglašen u API-ju, tretira se kao steel osim ako postoji
        # već vezana kategorija/instanca koja kaže drugačije.
        category = data.get('category') or getattr(self.instance, 'category', None)
        store = category.store if category else data.get('store') or getattr(self.instance, 'store', 'steel')

        # Način prodaje (na partial update čitaj sa postojeće instance)
        selling_mode = data.get('selling_mode')
        if selling_mode is None:
            selling_mode = getattr(self.instance, 'selling_mode', 'piece')

        is_on_request = (store == 'ambalaza' and selling_mode == 'on_request')

        if not is_on_request:
            price = data.get('price')
            if price is None:
                price = getattr(self.instance, 'price', None)
            if price is None or price <= 0:
                raise serializers.ValidationError(
                    {'price': ['Cena je obavezna i mora biti veća od 0.']}
                )

        return data

    def create(self, validated_data):
        """Override create da osigura da length_per_unit ima default vrednost"""
        if 'length_per_unit' not in validated_data or validated_data.get('length_per_unit') is None:
            validated_data['length_per_unit'] = 6.0
        if validated_data.get('category'):
            validated_data['store'] = validated_data['category'].store
        if validated_data.get('selling_mode') == 'on_request':
            validated_data['price'] = None
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Override update da osigura da length_per_unit ima default vrednost"""
        if 'length_per_unit' not in validated_data or validated_data.get('length_per_unit') is None:
            if hasattr(instance, 'length_per_unit') and instance.length_per_unit is not None:
                validated_data['length_per_unit'] = instance.length_per_unit
            else:
                validated_data['length_per_unit'] = 6.0
        if validated_data.get('category'):
            validated_data['store'] = validated_data['category'].store
        if validated_data.get('selling_mode') == 'on_request':
            validated_data['price'] = None
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        """Override to_representation da osigura da length_per_unit uvek ima vrednost"""
        data = super().to_representation(instance)
        # Osiguraj da length_per_unit uvek ima vrednost
        if 'length_per_unit' not in data or data['length_per_unit'] is None:
            data['length_per_unit'] = str(6.0)
        # Konvertuj Decimal u string za JSON serializaciju
        if 'length_per_unit' in data and isinstance(data['length_per_unit'], (int, float)):
            data['length_per_unit'] = str(float(data['length_per_unit']))
        return data


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True, allow_null=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True, allow_null=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    sold_by_length = serializers.SerializerMethodField()
    selling_mode = serializers.SerializerMethodField()
    package_size = serializers.SerializerMethodField()
    effective_length_per_unit = serializers.SerializerMethodField()

    def get_sold_by_length(self, obj):
        """Vraća da li je proizvod prodavan po metraži"""
        try:
            if obj.product:
                if hasattr(obj.product, 'selling_mode') and obj.product.selling_mode == 'length':
                    return True
                if hasattr(obj.product, 'sold_by_length'):
                    return obj.product.sold_by_length
        except (AttributeError, ValueError):
            pass
        return False

    def get_selling_mode(self, obj):
        try:
            if obj.product and hasattr(obj.product, 'selling_mode'):
                return obj.product.selling_mode
        except (AttributeError, ValueError):
            pass
        return 'piece'

    def get_package_size(self, obj):
        try:
            if obj.product and hasattr(obj.product, 'package_size'):
                return obj.product.package_size
        except (AttributeError, ValueError):
            pass
        return 1

    def get_effective_length_per_unit(self, obj):
        """Vraća efektivnu dužinu po jedinici (iz varijante ili proizvoda)"""
        try:
            if obj.variant and hasattr(obj.variant, 'effective_length_per_unit'):
                length = obj.variant.effective_length_per_unit
                if length is not None:
                    return length
            if obj.product and hasattr(obj.product, 'length_per_unit'):
                length = obj.product.length_per_unit
                if length is not None:
                    return length
        except (AttributeError, ValueError):
            pass
        return None

    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_name', 'variant', 'variant_name',
            'quantity', 'unit_price', 'total_price',
            'sold_by_length', 'selling_mode', 'package_size', 'effective_length_per_unit'
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    stores = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'store', 'stores', 'customer_name', 'customer_phone', 'customer_email',
            'address', 'city', 'notes', 'status', 'total_amount',
            'items', 'created_at', 'updated_at'
        ]

    def get_stores(self, obj):
        """Vraća sve prodavnice prisutne u stavkama narudžbine (za mešovite narudžbine)."""
        stores = set()
        for item in obj.items.all():
            if item.product_id and item.product and item.product.store:
                stores.add(item.product.store)
        # Fallback na store same narudžbine ako stavke nemaju proizvod (obrisan)
        if not stores and obj.store:
            stores.add(obj.store)
        return sorted(stores)


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=True
    )

    # Lista gradova u Republici Srbiji
    SERBIAN_CITIES = [
        'Beograd', 'Novi Sad', 'Niš', 'Kragujevac', 'Subotica', 'Zrenjanin', 'Pančevo',
        'Čačak', 'Novi Pazar', 'Kraljevo', 'Smederevo', 'Leskovac', 'Valjevo', 'Kruševac',
        'Vranje', 'Šabac', 'Užice', 'Sombor', 'Požarevac', 'Pirot', 'Zaječar', 'Kikinda',
        'Sremska Mitrovica', 'Jagodina', 'Vršac', 'Bor', 'Prokuplje', 'Loznica', 'Smederevska Palanka',
        'Inđija', 'Vrbas', 'Ruma', 'Bačka Palanka', 'Stara Pazova', 'Kovin', 'Aranđelovac',
        'Obrenovac', 'Lazarevac', 'Mladenovac', 'Batajnica', 'Surčin', 'Barajevo', 'Grocka',
        'Palilula', 'Zvezdara', 'Voždovac', 'Savski Venac', 'Stari Grad', 'Vračar', 'Novi Beograd',
        'Zemun', 'Surčin', 'Čukarica', 'Rakovica', 'Sopot', 'Gradska opština', 'Opština'
    ]

    class Meta:
        model = Order
        fields = [
            'store', 'customer_name', 'customer_phone', 'customer_email',
            'address', 'city', 'notes', 'items'
        ]
        extra_kwargs = {
            'customer_name': {'required': True},
            'customer_phone': {'required': True},
            'customer_email': {'allow_null': True, 'allow_blank': True, 'required': False},
            'address': {'required': True},
            'city': {'required': True},
            'notes': {'allow_null': True, 'allow_blank': True, 'required': False},
        }
    
    def validate_city(self, value):
        """Validacija da je grad u Republici Srbiji"""
        if not value or not value.strip():
            raise serializers.ValidationError("Grad je obavezan")
        
        city_normalized = value.strip().title()
        
        # Proveri da li je grad u listi (case-insensitive)
        if city_normalized not in [c.title() for c in self.SERBIAN_CITIES]:
            # Dozvoli i druge gradove ako su validni (može biti manji grad)
            # Ali proveri da nije očigledno van Srbije
            invalid_cities = ['Zagreb', 'Ljubljana', 'Sarajevo', 'Podgorica', 'Skopje', 'Tirana', 'Sofia', 'Bucharest', 'Budapest']
            if city_normalized in invalid_cities:
                raise serializers.ValidationError("Dostava je moguća samo na teritoriji Republike Srbije")
        
        return city_normalized
    
    def validate(self, data):
        # Konvertuj prazne stringove u None za opciona polja
        if 'customer_email' in data and data['customer_email'] == '':
            data['customer_email'] = None
        if 'notes' in data and data['notes'] == '':
            data['notes'] = None
        if 'address' in data:
            data['address'] = data['address'].strip()
        if 'city' in data:
            data['city'] = data['city'].strip()
        return data
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # First calculate total_amount
        total_amount = 0
        items_to_create = []
        
        for item_data in items_data:
            product_id = item_data.get('product') or item_data.get('product_id')
            variant_id = item_data.get('variant') or item_data.get('variant_id')
            # Convert quantity to Decimal to support decimal quantities for products sold by length
            from decimal import Decimal
            quantity = Decimal(str(item_data.get('quantity', 1)))
            
            # Get product and variant
            product = None
            variant = None
            
            if product_id:
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    pass
            
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id)
                except ProductVariant.DoesNotExist:
                    pass
            
            # Calculate price
            if variant:
                unit_price = variant.final_price
                if not product and hasattr(variant, 'product') and variant.product:
                    product = variant.product
                product_name = product.name if product else (variant.product.name if hasattr(variant, 'product') and variant.product else 'Unknown Product')
                variant_name = variant.name
            elif product:
                unit_price = product.current_price or 0
                product_name = product.name
                variant_name = ''
            else:
                unit_price = item_data.get('unit_price', 0)
                product_name = item_data.get('product_name', 'Unknown Product')
                variant_name = item_data.get('variant_name', '')

            if product and product.selling_mode == 'on_request':
                unit_price = 0
            
            total_price = unit_price * quantity
            total_amount += total_price
            
            # Store item data for creation
            items_to_create.append({
                'product': product,
                'variant': variant,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
                'product_name': product_name,
                'variant_name': variant_name
            })
        
        # Create order with total_amount
        order = Order.objects.create(
            **validated_data,
            total_amount=total_amount if total_amount > 0 else None
        )
        
        # Create OrderItems
        for item_data in items_to_create:
            OrderItem.objects.create(
                order=order,
                **item_data
            )
        
        return order


class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Serializer za kontakt poruke
    """
    class Meta:
        model = ContactMessage
        fields = ['id', 'store', 'name', 'email', 'phone', 'message', 'is_read', 'is_replied', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'email': {'required': False, 'allow_blank': True, 'allow_null': True},
            'phone': {'required': False, 'allow_blank': True, 'allow_null': True},
        }

    def validate(self, data):
        """
        Proveri da je bar jedno od email ili phone popunjeno
        Samo pri kreiranju, ne pri update-u
        """
        # Ako je partial update (PATCH), preskoči validaciju
        if self.partial:
            return data

        # Ako je update (PUT), uzmi postojeće vrednosti iz instance
        if self.instance:
            email = data.get('email', self.instance.email)
            phone = data.get('phone', self.instance.phone)
        else:
            # Novo kreiranje
            email = data.get('email')
            phone = data.get('phone')

        if not email and not phone:
            raise serializers.ValidationError(
                'Morate navesti bar email ili telefon.'
            )

        return data
