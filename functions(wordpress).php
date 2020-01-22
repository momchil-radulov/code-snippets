/*
* Create a order on create customer or by web api - WooCommerce plugin.
* https://codetrycatch.com/create-a-woocommerce-order-programatically/
* How to use: https://my-site/wp-admin/admin-ajax.php?action=my_action
*/
function create_order($user_id = 0) {
	if ($user_id == 0)
		$user_id = get_current_user_id();
	$address = array(
                'first_name' => get_user_meta($user_id, 'billing_first_name', true),
                'last_name' => get_user_meta($user_id, 'billing_last_name', true),
                'address_1' => get_user_meta($user_id, 'billing_address_1', true),
                'address_2' => get_user_meta($user_id, 'billing_address_2', true),
                'company' => get_user_meta($user_id, 'billing_company', true),
                'email' => get_user_meta($user_id, 'billing_email', true),
                'phone' => get_user_meta($user_id, 'billing_phone', true),
                'country' => get_user_meta($user_id, 'billing_country', true),
                'state' => get_user_meta($user_id, 'billing_state', true),
                'postcode' => get_user_meta($user_id, 'billing_postcode', true),
                'city' => get_user_meta($user_id, 'billing_city', true),
            );

	$order = wc_create_order();
	$order->add_product( get_product( '2308' ), 1 ); //(get_product with id and next is for quantity)
	$order->set_address( $address, 'billing' );
	$order->set_address( $address, 'shipping' );
	$order->set_customer_id($user_id);
	$order->calculate_totals();
}

function my_action() {
	global $wpdb;
	$user_id = get_current_user_id();
	create_order(0);
    	echo 'create_order(); ';
	echo '$user_id = ' . $user_id;
	wp_die();
}
add_action( 'wp_ajax_my_action', 'my_action' );
add_action( 'wp_ajax_nopriv_my_action', 'my_action' );

function user_register_add_order( $user_id ) {
	create_order($user_id);
}

function sv_link_orders_at_registration( $user_id ) {
	create_order($user_id);
	wc_update_new_customer_past_orders( $user_id );
}

add_action( 'woocommerce_created_customer', 'sv_link_orders_at_registration' );
add_action( 'user_register', 'user_register_add_order' );

/*
* Automatically adding the product to the cart - WooCommerce plugin.
* https://wordpress.org/support/topic/how-can-i-automatically-add-product-when-user-registered-in-wordpress/
*/
function aaptc_add_product_to_cart() {
    if ( ! is_admin() ) {
        $product_id = 2305;  // Product Id of the free product which will get added to cart
        $found 	= false;
        //check if product already in cart
        if ( sizeof( WC()->cart->get_cart() ) > 0 ) {
            foreach ( WC()->cart->get_cart() as $cart_item_key => $values ) {
                $_product = $values['data'];
                if ( $_product->get_id() == $product_id )
                    $found = true;
            }
            // if product not found, add it
            if ( ! $found )
                WC()->cart->add_to_cart( $product_id );
        } else {
            // if no products in cart, add it
            WC()->cart->add_to_cart( $product_id );
        }
    }    
}
add_action( 'init', 'aaptc_add_product_to_cart' );

/*
* Show orders only for assigned users, except only admins - WooCommerce plugin.
* https://stackoverflow.com/questions/45879418/how-can-i-assign-an-order-to-a-certain-shop-manager-in-woocommerce
*/
function custom_admin_shop_manager_orders($query) {
	global $pagenow;
	$qv = &$query->query_vars;

	$currentUserRoles = wp_get_current_user()->roles;
	//$meta = get_post_meta( get_the_ID() );
	//$meta = get_post_custom();
	//echo_log('123123123');
	//echo_log($meta);
	//echo_log($currentUserRoles);
	$user_id = get_current_user_id();
  if (!in_array('administrator', $currentUserRoles)) {
    if ( $pagenow == 'edit.php' && 
      isset($qv['post_type']) && $qv['post_type'] == 'shop_order' ) {
      // I use the meta key from step 1 as a second parameter here
      $query->set('meta_key', '[wpuef] test');
      // The value we want to find is the $user_id defined above
      $query->set('meta_value', $user_id);
    }
  }
	return $query;
}
function echo_log( $what ) // https://stackoverflow.com/questions/14541989/how-do-i-debug-a-wordpress-plugin
{
    echo '<pre>'.print_r( $what, true ).'</pre>';
}
add_filter('pre_get_posts', 'custom_admin_shop_manager_orders');
