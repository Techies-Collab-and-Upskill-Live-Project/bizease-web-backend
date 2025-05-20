from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
]

# MAIN: USER CRUD; PRODUCT CRUD;

"""
-- what range of characters should I accept as valid in character fields?

User Table
 - id PRIMARY KEY
 - Business Name VARCHAR (200) NOT NULL 
 - Full Name VARCHAR (200) NOT NULL
 - Email Address VARCHAR (200) NOT NULL
 - Business Email  VARCHAR(200) -- not part of sign up fields but present in business info
 - Currency ENUM TYPE NOT NULL
 - Business Type ENUM TYPE NOT NULL -- needs more explanation
 - Password VARCHAR(20) NOT NULL
 - Country Enum NOT NULL
 - State Enum NOT NULL

Preference Table
 - id PRIMARY KEY
 - rcv_mail_for_new_orders BOOLEAN DEFAULT=false
 - rcv_mail_for_low_stocks BOOLEAN DEFAULT=false

 - rcv_whatsapp_notification BOOLEAN DEFAULT=false
 - rcv_mail_notification BOOLEAN DEFAULT=false
 - rv_msg_notification BOOLEAN DEFAULT=false

 - low_stock_alert_threshold INTEGER DEFAULT 5 NOT NULL
 - init_order_status ENUM (pending, delivered, shipped)  -- are there any other types to be added to the enum?

 - Language ENUM () -- what languages do we support?

Order Table
 - id PRIMARY KEY
 - client_name NOT NULL
 - client_email
 - client_phone
 - order status
 - order date

Ordered Product
 - id PRIMARY KEY
 - order_id
 - name
 - quantity
 - (order_id, name)  unique

Products Table
 - id PRIMARY KEY
 - name
 - description -- present in 'add/edit form' but not used anywhere the data is actually displayed
 - category -- present in displayed products but no interface to 'add/edit' this field. 
   I ask these questions to know if they are actually required fields in the database. 
   This also lets me know the exact field/data I'm expecting on the backend so I can 
   properly validate data mutating requests before sending a response to the client on the backend.
   An unused field should be dropped too as It's just a waste of space and Makes the whole schema messy
 - stock_level Integer
 - ID No Integer -- I don't know the purpose of this field
 - Last Update -- Automatic date field
 - price integer

Task
 - Name
 - category
 - due_date
 - status
 - priority
 - notes


"""