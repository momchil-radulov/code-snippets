<?php
########################
###  some functions  ###
########################

# custom useful functions
# arr_get, obj_get
# fmt_bgn

function safe_print($variable = null, $is_safe_html = false) {
    if (!isset($variable)) {
        print ''; // Ако променливата не е дефинирана, извежда празен стринг
        return;
    }
    
    if (is_null($variable)) {
        print ''; // Ако е null, извежда празен стринг
    } elseif (is_bool($variable)) {
        print $variable ? 'true' : 'false'; // Ако е булева стойност
    } elseif (is_array($variable) || is_object($variable)) {
        print $is_safe_html 
            ? htmlspecialchars(json_encode($variable), ENT_QUOTES, 'UTF-8') 
            : json_encode($variable); // Преобразува масив/обект в JSON
    } elseif (is_scalar($variable)) {
        print $is_safe_html 
            ? htmlspecialchars((string)$variable, ENT_QUOTES, 'UTF-8') 
            : (string)$variable; // Преобразува скаларни стойности
    } else {
        print ''; // Всички други случаи (например ресурси)
    }
}

function debug_print($data, $exit = false, $logToFile = false)
{
    $backtrace = debug_backtrace();
    echo "function " . $backtrace[0]['function'] . ", file " . $backtrace[0]['file'] . ", line " . $backtrace[0]['line'] . "\n\n";

    echo '<pre style="background-color: #f9f9f9; padding: 10px; border: 1px solid #ddd; font-size: 14px;">';
    print_r($data);
    echo '</pre>';

    if($logToFile) {
        file_put_contents('debug_log.txt', print_r($data, True) . "\n", FILE_APPEND);
    }

    if($exit) {
        exit('debug_print exit');
    }
}

function print_stack_trace($is_args=false) {
    $stack = debug_backtrace();
    echo "<pre>";
    foreach ($stack as $frame) {
        if (isset($frame['file'])) {
            echo "Файл: " . $frame['file'] . "\n";
        }
        if (isset($frame['line'])) {
            echo "Ред: " . $frame['line'] . "\n";
        }
        echo "Функция: " . $frame['function'] . "\n";
        if ($is_args && isset($frame['args'])) {
            echo "Аргументи: ";
            print_r($frame['args']);
            echo "\n";
        }
        echo "\n";
    }
    echo "</pre>";
}

public function debug_trace() {
    $backtrace = debug_backtrace();
    
    echo "<pre>debug_trace:\n";
    foreach ($backtrace as $entry) {
        echo $entry['function'] . " < " . ($entry['file'] ?? 'N/A') . " : " . ($entry['line'] ?? 'N/A') . "\n";
    }
    echo "---------------------\n</pre>";
}

########################
### helper functions ###
########################

if ( ! function_exists('arr_get') )                                                                                                
{
    function arr_get($array, $key, $default = null) {
        return (array_key_exists($key, $array) && !empty($array[$key])) ? $array[$key] : $default;
    }
}

if ( ! function_exists('arr_init_key') )
{
    function arr_init_key(&$array, $key, $default) {
        if ( ! array_key_exists($key, $array)) {
            $array[$key] = $default;
        }
        return $array[$key];
    }
}

if ( ! function_exists('obj_get') )
{   
    function obj_get($object, $property, $default = null)
    {   
        if (property_exists($object, $property)) {
            return empty($object->$property) ? $default : $object->$property;
        }
        return $default;
    }
}

########################
###  some raw code   ###
########################

function some_code() {
    // в даден клас да проверим:
    if (method_exists($this, $methodName)) {
        echo "Методът '$methodName' съществува в класа.\n";
        $this->$methodName(); // Извикваме метода, ако съществува
    }
    $reflectionMethod = new ReflectionMethod($this, 'validate');
    echo "Методът 'validate' има " . $reflectionMethod->getNumberOfParameters() . " аргумента.\n";
    // извън класът
    if (method_exists($obj, 'exampleMethod')) {
        $obj->exampleMethod(); // Извикваме метода, ако съществува
    }
    $reflectionMethod = new ReflectionMethod('ClassName', 'methodName');

}
