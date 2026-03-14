FROM odoo:19

USER root

COPY ./custom_addons /mnt/extra-addons
COPY ./docker/odoo.conf /etc/odoo/odoo.conf

USER odoo
