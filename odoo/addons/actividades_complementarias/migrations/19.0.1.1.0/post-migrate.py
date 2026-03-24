import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    v1.0.0 → v1.1.0
    Adds jd_firmo and responsable_firmo columns to actividad_complementaria.
    These replace the old single constancias_firmadas boolean with a
    dual-signature model (both JD and Responsable must sign independently).

    constancias_firmadas is now a stored computed field — Odoo will recreate
    it automatically. We only need to seed the two new raw columns.
    """
    _logger.info("Migration 19.0.1.1.0: adding dual-signature columns")

    cr.execute("""
        ALTER TABLE actividad_complementaria
        ADD COLUMN IF NOT EXISTS jd_firmo BOOLEAN NOT NULL DEFAULT FALSE
    """)

    cr.execute("""
        ALTER TABLE actividad_complementaria
        ADD COLUMN IF NOT EXISTS responsable_firmo BOOLEAN NOT NULL DEFAULT FALSE
    """)

    # Preserve existing data: if constancias_firmadas was already True on a
    # record, treat it as both parties having signed (best-effort migration).
    cr.execute("""
        UPDATE actividad_complementaria
        SET jd_firmo = TRUE, responsable_firmo = TRUE
        WHERE constancias_firmadas = TRUE
    """)

    cr.execute("SELECT COUNT(*) FROM actividad_complementaria WHERE jd_firmo = TRUE")
    migrated = cr.fetchone()[0]
    _logger.info(
        "Migration 19.0.1.1.0 complete: %d records migrated with dual-signature flags",
        migrated,
    )
