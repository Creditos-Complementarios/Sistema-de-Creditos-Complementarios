FROM odoo:19.0

USER root

# Install extra Python dependencies for custom addons (if any)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Custom addons — path relative to repo root (build context)
RUN mkdir -p /mnt/extra-addons
COPY odoo/addons/ /mnt/extra-addons/

# Odoo config — path relative to repo root (build context)
COPY infrastructure/config/odoo.conf /etc/odoo/odoo.conf

USER odoo

CMD ["odoo"]
