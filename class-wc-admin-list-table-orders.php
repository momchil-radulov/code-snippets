url (to show woocommerce orders):
https://your-site.com/wp-admin/edit.php?post_type=shop_order

file:
/wp-content/plugins/woocommerce/includes/admin/list-tables/class-wc-admin-list-table-orders.php

function:
render_order_date_column()

append code:
$user  = get_user_by( 'id', $this->object->get_customer_id() );
echo $user->user_login;
echo '<img src="https://media.gettyimages.com/photos/blue-sky-and-white-clouds-picture-id1096877588">';
