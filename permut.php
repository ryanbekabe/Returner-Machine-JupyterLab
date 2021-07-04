<?php
//$a = array("1", "2");
$b = array("hello", "test");
$c = array("_x", "_y");

if(is_array($a)){
$aG = array($a,$b, $c);
}else{
$aG = array($b, $c);
    }
$codes = array();
$pos = 0;
generateCodes($aG);

function generateCodes($arr) {
    global $codes, $pos;
    if(count($arr)) {
        for($i=0; $i<count($arr[0]); $i++) {
            $tmp = $arr;
            $codes[$pos] = $arr[0][$i];
            $tarr = array_shift($tmp);
            $pos++;
            generateCodes($tmp);

        }
    } else {
        echo join("", $codes)."<br/>";
    }
    $pos--;
}
?>