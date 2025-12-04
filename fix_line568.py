#!/usr/bin/env python
"""Quick fix for admin.py line 568 indentation error"""

file_path = r'c:\New folder\New folder\Chrome Downloads\New folder\Portfolio Site\routes\admin.py'

# Read all lines
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix lines 560-577 (0-indexed: 559-576)
# The issue is orphaned code from lines 568-577
# We need to properly close edit_blog_post and add delete_blog_post

fixed_lines = lines[:559]  # Keep everything before line 560

# Add the corrected edit_blog_post ending
fixed_lines.extend([
    '        if post.title != request.form.get(\'title\'):\r\n',
    '            post.slug = create_slug(request.form.get(\'title\'))\r\n',
    '        \r\n',
    '        # Handle image upload if new image provided\r\n',
    '        if \'image\' in request.files and request.files[\'image\'].filename:\r\n',
    '            post.image = save_file(request.files[\'image\'])\r\n',
    '        \r\n',
    '        db.session.commit()\r\n',
    '        flash(\'Blog post updated successfully!\', \'success\')\r\n',
    '        return redirect(url_for(\'admin.blog_posts\'))\r\n',
    '    \r\n',
    '    return render_template(\'admin/blog/edit.html\', post=post)\r\n',
    '\r\n',
    '@admin_bp.route(\'/blog/delete/<int:post_id>\', methods=[\'POST\'])\r\n',
    '@login_required\r\n',
    'def delete_blog_post(post_id):\r\n',
    '    post = BlogPost.query.get_or_404(post_id)\r\n',
    '    \r\n',
    '    # Delete post image if it exists\r\n',
    '    if post.image:\r\n',
    '        try:\r\n',
    '            image_path = os.path.join(current_app.config[\'UPLOAD_FOLDER\'], post.image.split(\'/\')[-1])\r\n',
    '            if os.path.exists(image_path):\r\n',
    '                os.remove(image_path)\r\n',
    '        except Exception as e:\r\n',
    '            print(f\"Error deleting image: {e}\")\r\n',
    '    \r\n',
    '    db.session.delete(post)\r\n',
    '    db.session.commit()\r\n',
    '    \r\n',
    '    flash(\'Blog post deleted successfully!\', \'success\')\r\n',
    '    return redirect(url_for(\'admin.blog_posts\'))\r\n',
])

# Add everything after line 577 (0-indexed: 577)
fixed_lines.extend(lines[577:])

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("Fixed admin.py - edit_blog_post and delete_blog_post functions corrected")
