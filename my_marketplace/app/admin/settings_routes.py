from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from my_marketplace.app.admin import admin_bp
from models import SiteSetting
from .forms import SettingsForm
from my_marketplace.app.database import db

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))

    site_setting = SiteSetting.query.first()
    if not site_setting:
        site_setting = SiteSetting()
        db.session.add(site_setting)
        db.session.commit()

    form = SettingsForm(obj=site_setting)

    if form.validate_on_submit():
        form.populate_obj(site_setting)
        db.session.commit()
        flash('Site settings have been updated.', 'success')
        return redirect(url_for('admin.settings'))

    return render_template('admin/settings.html', form=form, title='Site Settings')