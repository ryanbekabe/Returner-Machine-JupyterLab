<?php
//php7
$servername = "localhost:3306";
$username = "root";
$password = "bismillah";
$dbname = "hanyajasa";

/*
CREATE TABLE `tb_uploadv3` (
  `id` int(11) NOT NULL,
  `cname` varchar(500) NOT NULL,
  `md5` varchar(200) NOT NULL,
  `sha256` varchar(200) NOT NULL,
  `csize` varchar(500) NOT NULL,
  `ctype` varchar(500) NOT NULL,
  `cerror` varchar(500) NOT NULL,
  `cmove` varchar(500) NOT NULL,
  `cforbidden` varchar(500) NOT NULL,
  `cdate` varchar(500) NOT NULL,
  `cip` varchar(500) NOT NULL,
  `cagent` varchar(500) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `tb_uploadv3` (`id`, `cname`, `md5`, `sha256`, `csize`, `ctype`, `cerror`, `cmove`, `cforbidden`, `cdate`, `cip`, `cagent`) VALUES
(1, 'geo.txt', '', '', '2204', 'text/plain', '0', '1', '0', '2019-03-01 17:55:38', '182.1.193.83', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'),
(2, 'geo.txt', '', '', '2204', 'text/plain', '0', '1', '0', '2019-03-02 08:01:02', '114.125.220.220', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36');

ALTER TABLE `tb_uploadv3`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `tb_uploadv3`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
COMMIT;
*/

$waktupengiriman=date("YmdHis");
$ip=$_SERVER['REMOTE_ADDR'];
$ua=$_SERVER['HTTP_USER_AGENT'];
$nameRAW='-waktu='.$waktupengiriman.'-ip='.$ip.'-useragent='.$ua;

$filename = $_FILES["file"]["name"];
$temp = explode(".", $_FILES["file"]["name"]);

if($filename=="")
{
    echo "Harap tentukan file untuk diupload!! <br>";
    echo '    <br><input type="submit" value="Ulang (Reload)"
    onclick="window.location=\'https://hanyajasa.com/byteentropy\';" />
    ';
    exit;
}

$extension = "";

$filemove = 0;
$fileforbidden = 0;

if (count($temp) > 1)
{
    $extension = "." . strtolower(end($temp));
    $original_ext = strtolower(end($temp));
}

$name = substr($filename, 0, strlen($filename) - strlen($extension));

if ($_FILES["file"]["error"] > 0)
{
   // echo "Return Code: " . $_FILES["file"]["error"] . "<br>";
    echo 'Harap tentukan file untuk diupload. <br>';
    echo '<br><input type="submit" value="Ulang (Reload)" onclick="window.location=\'https://hanyajasa.com/byteentropy\';"/> ';
    exit;
}
else
{
    echo "<br>File $filename sudah kami proses dan berikut hasilnya...";
    $i = 0;
    for ($i = 0; $i<=100; $i++)
    {
        if ($i == 0)
            $new_name =$name .  $extension;
            //$new_name_spy =$name.$nameRAW .  $extension;
        else
            $new_name =$name . "_" . $i . $extension;
            //$new_name_spy =$name.$nameRAW . "_" . $i . $extension;
        if (file_exists("entropybin/" . $new_name)) {
                //repeat
        } else {
            break;
        }
    }

    global $varmd5, $varsha256;
    $filemove = move_uploaded_file($_FILES["file"]["tmp_name"], "entropybin/" . $new_name);
    $varfilename = "entropybin/".$new_name;
    $varmd5 = hash_file('md5',$varfilename);
    $varsha256 = hash_file('sha256',$varfilename);
}
mkdir("/var/www/html/byteentropy/entropybin/".$varmd5,0700);
$targetFile = "/var/www/html/byteentropy/entropybin/".$varmd5."/report.txt";
$VarHeader = "MD5 File: ".$varmd5."\n"."Nama File: ".$new_name."\n"."@: ".$waktupengiriman."\n";
echo "<br/>Rangkuman Laporan: https://hanyajasa.com/byteentropy/entropybin/".$varmd5."/report.txt";
$output = shell_exec('/usr/bin/python3.6 /var/www/html/byteentropy/entropy.py /var/www/html/byteentropy/entropybin/'.$new_name); 
echo "<pre>$output</pre>";
file_put_contents($targetFile, $VarHeader.$output);
$filesize = $_FILES["file"]["size"];
$filetype = $_FILES["file"]["type"];
$fileerror = $_FILES["file"]["error"];

$WaktuNowBekabe=date('Y-m-d H:i:s');

$conn = mysqli_connect($servername, $username, $password, $dbname);
// Check connection
if (!$conn) {
    //die("Connection failed: " . mysqli_connect_error());
}

$sql = "INSERT INTO tb_uploadv3 (cname, csize, md5, sha256, ctype, cerror, cmove, cforbidden, cdate, cip, cagent) VALUES('$filename', '$filesize', '$varmd5', '$varsha256', '$filetype', '$fileerror', '$filemove', '$fileforbidden',
'$WaktuNowBekabe', '$ip', '$ua')";

if (mysqli_query($conn, $sql)) {
    //echo "New record created successfully";
} else {
    //echo "Error: " . $sql . "<br>" . mysqli_error($conn);
}
mysqli_close($conn);

echo '<br><input type="submit" value="Tambah File (Add)"
onclick="window.location=\'https://hanyajasa.com/byteentropy\';" />
';
?>
<br/>
<br/>.<br/>
<br/>..<br/>