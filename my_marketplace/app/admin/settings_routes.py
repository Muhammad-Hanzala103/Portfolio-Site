from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from my_marketplace.app.admin import admin_bp
from models import SiteSetting, db
from forms import SettingsForm

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def manage_settings():
    if current_user.role != 'admin':
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('main.index'))

    settings = SiteSetting.query.all()
    settings_dict = {setting.key: setting.value for setting in settings}

    form = SettingsForm(data=settings_dict)

    if form.validate_on_submit():
        for key, value in form.data.items():
            if key not in ['csrf_token', 'submit']:
                setting = SiteSetting.query.filter_by(key=key).first()
                if setting:
                    setting.value = value
                else:
                    setting = SiteSetting(key=key, value=value)
                    db.session.add(setting)
        db.session.commit()
        flash('Site settings updated successfully!', 'success')
        return redirect(url_for('admin.manage_settings'))

    return render_template('settings.html', form=form)