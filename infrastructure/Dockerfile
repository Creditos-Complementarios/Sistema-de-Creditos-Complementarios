FROM odoo:19.0

USER root

# Install extra Python dependencies for custom addons (if any)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Custom addons
RUN mkdir -p /mnt/extra-addons
COPY addons/ /mnt/extra-addons/

# Odoo config
COPY config/odoo.conf /etc/odoo/odoo.conf

USER odoo

CMD ["odoo"]
