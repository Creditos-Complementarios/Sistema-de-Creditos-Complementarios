/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, useRef } from "@odoo/owl";

const STORAGE_KEY = "ac_dark_mode";
const MODULE_PREFIX = "actividades_complementarias";

class DarkModeToggle extends Component {
    setup() {
        this.checkboxRef = useRef("checkbox");

        onMounted(() => {
            // Restaurar estado guardado
            const saved = localStorage.getItem(STORAGE_KEY) === "true";
            if (this.checkboxRef.el) {
                this.checkboxRef.el.checked = saved;
            }
            this._applyDarkMode(saved);

            // Observar cambios de menú activo
            this._observer = new MutationObserver(() => {
                const saved = localStorage.getItem(STORAGE_KEY) === "true";
                this._applyDarkMode(saved);
            });
            this._observer.observe(document.body, {
                attributes: true,
                subtree: true,
                attributeFilter: ["data-menu-xmlid"],
            });
        });
    }

    _isModuleActive() {
        const brand = document.querySelector(".o_menu_brand");
        return brand?.dataset?.menuXmlid?.startsWith(MODULE_PREFIX) ?? false;
    }

    _applyDarkMode(isDark) {
        if (isDark && this._isModuleActive()) {
            document.body.classList.add("ac_dark_mode");
        } else {
            document.body.classList.remove("ac_dark_mode");
        }
    }

    toggleDarkMode(ev) {
        const isChecked = ev.target.checked;
        localStorage.setItem(STORAGE_KEY, isChecked);
        this._applyDarkMode(isChecked);
    }
}

DarkModeToggle.template = "actividades_complementarias.DarkModeToggle";

registry.category("systray").add("actividades_dark_mode", {
    Component: DarkModeToggle,
    sequence: 100,
});