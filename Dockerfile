FROM odoo:19

USER root

# crear carpeta de addons personalizados
RUN mkdir -p /mnt/custom-addons

# copiar addons
COPY custom_addons /mnt/custom-addons

# copiar configuración
COPY docker/odoo.conf /etc/odoo/odoo.conf

USER odoo

CMD ["odoo", "-i", "base", "--without-demo=all"]
