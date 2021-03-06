# Generated by Django 2.1.5 on 2019-02-08 04:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0010_auto_20190202_2240'),
        ('orders', '0003_offer'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='OrderItem',
            new_name='OfferItem',
        ),
        migrations.RemoveField(
            model_name='offer',
            name='book',
        ),
        migrations.RemoveField(
            model_name='offeritem',
            name='order',
        ),
        migrations.AddField(
            model_name='offeritem',
            name='offer',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='item', to='orders.Offer'),
            preserve_default=False,
        ),
    ]
