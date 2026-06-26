from django.db import migrations, models


def set_selling_modes(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    for product in Product.objects.filter(sold_by_length=True):
        product.selling_mode = 'length'
        product.save(update_fields=['selling_mode'])


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0025_alter_product_options_product_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='store',
            field=models.CharField(choices=[('steel', 'Gvožđara'), ('ambalaza', 'Ambalaža')], default='steel', max_length=20),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='store',
            field=models.CharField(blank=True, choices=[('steel', 'Gvožđara'), ('ambalaza', 'Ambalaža')], default='steel', max_length=20),
        ),
        migrations.AddField(
            model_name='order',
            name='store',
            field=models.CharField(choices=[('steel', 'Gvožđara'), ('ambalaza', 'Ambalaža')], default='steel', max_length=20),
        ),
        migrations.AddField(
            model_name='product',
            name='dimensions',
            field=models.CharField(blank=True, help_text='Dimenzije proizvoda (npr. 500ml)', max_length=200),
        ),
        migrations.AddField(
            model_name='product',
            name='package_size',
            field=models.PositiveIntegerField(default=1, help_text='Broj komada u jednom pakovanju (za prodaju po pakovanju)'),
        ),
        migrations.AddField(
            model_name='product',
            name='selling_mode',
            field=models.CharField(
                choices=[
                    ('piece', 'Po komadu'),
                    ('length', 'Po metraži'),
                    ('package', 'Po pakovanju'),
                    ('weight', 'Po kilogramu'),
                    ('on_request', 'Na upit'),
                ],
                default='piece',
                help_text='Način prodaje proizvoda',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='store',
            field=models.CharField(choices=[('steel', 'Gvožđara'), ('ambalaza', 'Ambalaža')], default='steel', max_length=20),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='order',
            name='total_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='slug',
            field=models.SlugField(blank=True, help_text='SEO-friendly URL (auto-generiše se iz naziva)', max_length=250),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('store', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='product',
            unique_together={('store', 'slug')},
        ),
        migrations.RunPython(set_selling_modes, migrations.RunPython.noop),
    ]
