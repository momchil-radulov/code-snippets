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
