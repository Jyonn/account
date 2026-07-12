from django.db import migrations


def sync_cli_device_grant_columns(apps, schema_editor):
    model = apps.get_model('User', 'CLIDeviceGrant')
    table_name = model._meta.db_table
    connection = schema_editor.connection

    existing_columns = {
        column.name
        for column in connection.introspection.get_table_description(connection.cursor(), table_name)
    }

    for field_name in ['request_type', 'app_id', 'auth_code', 'redirect_uri']:
        if field_name in existing_columns:
            continue
        field = model._meta.get_field(field_name)
        schema_editor.add_field(model, field)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('User', '0033_clidevicegrant'),
    ]

    operations = [
        migrations.RunPython(sync_cli_device_grant_columns, migrations.RunPython.noop),
    ]
