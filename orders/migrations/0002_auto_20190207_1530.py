# Generated by Django 2.1.5 on 2019-02-07 23:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0010_auto_20190202_2240'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='books.Book')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='item', to='orders.Order')),
            ],
        ),
        migrations.RemoveField(
            model_name='offerbook',
            name='book',
        ),
        migrations.RemoveField(
            model_name='offerbook',
            name='offer',
        ),
        migrations.DeleteModel(
            name='OfferBook',
        ),
    ]
