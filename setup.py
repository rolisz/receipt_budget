from distutils.core import setup

setup(
    name='receipt_budget',
    version='0.6',
    packages=['receipts.receipts', 'receipts.receipts-app'],
    url='https://github.com/rolisz/receipt_budget',
    license='BSD',
    author='Roland',
    author_email='rolisz@gmail.com',
    description='An application for managing expenses and doing OCR on receipts',
    requires=[
        'django (>= 1.5)', 'scikitlearn', 'SimpleCV', 'django-tokenapi',
        'django-userena', 'django_extensions', 'geopy'
    ]
)
