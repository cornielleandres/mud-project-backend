# Generated by Django 2.1.7 on 2019-03-25 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mud', '0005_auto_20190324_1439'),
    ]

    operations = [
        migrations.CreateModel(
            name='Monster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='default monster name', max_length=32, unique=True)),
                ('hp', models.IntegerField(default=100)),
                ('attack', models.IntegerField(default=50)),
                ('defense', models.IntegerField(default=50)),
            ],
        ),
        migrations.AddField(
            model_name='player',
            name='attack',
            field=models.IntegerField(default=25),
        ),
        migrations.AddField(
            model_name='player',
            name='defense',
            field=models.IntegerField(default=25),
        ),
        migrations.AddField(
            model_name='player',
            name='hp',
            field=models.IntegerField(default=100),
        ),
    ]
