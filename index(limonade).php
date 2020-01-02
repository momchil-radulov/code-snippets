<?php
    require_once '../lib/limonade.php';
    dispatch      ('^/device/([a-z]{2}[0-9]+)$',        'list_device_by_key'  );
    dispatch_post ( '^/device/(cw[0-9]+)/settings/([0-9a-z_]+)/([0-9]+)$' , 'device_settings_post' );
    
    function configure ()
    {
        global $login_id;
        global $lang;
        
        option ( 'session' , false );
        option ( 'signature' , false ); // header X-Limonade
        option ( 'siteurl' , 'http://mom2000.com' );
        
        if ( isset ( $_COOKIE['LOGIN_ID'] ) ) {
            $login_id = $_COOKIE['LOGIN_ID'];
            set    ( 'login_id' , $login_id );
            option ( 'login_id' , $login_id );
        }
        else {
            $login_id = 'None';
            set    ( 'login_id' , 'None' );
            option ( 'login_id' , 'None' );
        }
        if ( isset ( $_GET['debug'] ) )
            option ( 'debug' , True );
        else
            option ( 'debug' , False );
            
        $lang = array();
        $lang['bg'] = array();
        $lang['en'] = array();
        $lang['de'] = array();
        $lang['ru'] = array();
        $lang['bg']['title'] = 'Главна страница';
        $lang['en']['title'] = 'Home page';
        $lang['de']['title'] = '...';
        $lang['ru']['title'] = '...';
    }
    
    function not_found($errno, $errstr, $errfile=null, $errline=null)
    {
        // return json ( array ( 'result' => 'not found' ) );
        // return '[]';
        return json ( array ( 'result' => false ,
                              'error' => 'not found route' )
                    );
    }
    
    function list_device_by_key()
    {
        $object_id = params( 0 );
        ...
        $result = array ();
        if ( $rows ) {
            while ( $row = $rows->fetchArray ( 1 ) ) {
              $result[] = $row;
              //array_push ( $result , $row );
              //var_dump ( $row );
            }
        }
        return json (  array ( 'result' => true ,
                               'devices' => $result )
                    );
    }
    
    function device_settings_post ()
    {
        $device_key = params (0);
        $setting = params (1);
        $value = params (2);
        ...
    }
