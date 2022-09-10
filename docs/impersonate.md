# Impersonate other users

Superusers can impersonate other users to see what they are seeing by going to the user management tools at `/admin/auth/user` and clicking 
the `Start` link in the `Impersonate` column.

Clicking `Stop` in the same column will stop the impersonation.

If you are currently impersonating a user a notification message will be displaed on all non django-admin pages stating that you are current
ly viewing things through another user.   

Django-admin views are excluded from impersonation.

Impersonations are propagated to all the fullctl services using this aaactl instance.
