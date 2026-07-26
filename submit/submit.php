<?php

require_once 'vendor/autoload.php';
use Mailgun\Mailgun;
$mgClient = Mailgun::create('apicodegoeshere', 'https://api.mailgun.net/v3/ylp.wtf');
$domain = "yagneshlp.me";
if ($_SERVER["REQUEST_METHOD"] == "POST") {
  $u_name = filter_var($_POST["name"], FILTER_SANITIZE_STRING);
  $u_email = filter_var($_POST["email"], FILTER_SANITIZE_EMAIL);
  $u_category = filter_var($_POST["category"], FILTER_SANITIZE_STRING);
  $u_desc = filter_var($_POST["desc"], FILTER_SANITIZE_STRING);
  $msgToClient = array(
    'from'    => 'Yagnesh L P <admin@yagneshlp.me>',
    'to'      => $u_email ,
    'subject' => 'RE: ' . $u_category ,
    'html'    => '<html>' .  '<body>' .     '  <h1> Hi '. $u_name . '</h1>' .     ' <br>Thanks for your interest in my services, I will get back to you within 24 Hours <br> <br> Yours Truly, <br> Yagnesh L P' .    ' </body>' .    '</html>'
  );
  $mgClient->messages()->send($domain, $msgToClient);
  $msgToMe = array(
    'from'    => 'Postman <postman@yagneshlp.me>',
    'to'      => 'yagneshlp@ylp.wtf' ,
    'subject' => 'An enquiry by ' . $u_name ,
    'text'    => 'Hey, someone Enquired about ' . $u_category . '. Their email is: ' . $u_email . '. Their needs are : ' . $u_desc
  );
  $mgClient->messages()->send($domain, $msgToMe);
include("emailsent.html");
}
else{
  include("../errorDocs/404errorr.html");
}
?>
