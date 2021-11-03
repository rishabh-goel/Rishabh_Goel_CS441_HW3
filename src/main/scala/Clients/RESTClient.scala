package Clients

import com.example.protos.hello.Output
import com.typesafe.config.ConfigFactory

import scala.concurrent.Future
import scala.util.{Failure, Success, Try}

object RESTClient {

  def main(args: Array[String]): Unit = {
    val params = args.headOption.mkString
    val parameters = params.split(",")
    val time = parameters(0)
    val delta = parameters(1)
    val conf = ConfigFactory.load("application")
    val url: String = conf.getString("randomLogGenerator.url")

    Try(scala.io.Source.fromURL(url+"/getLogCount?time="+time+"&delta="+delta)) match {
      case Success(response) => {
        val result = response.mkString
        val resultSplit = result.split(": ")
        val count = resultSplit(1).substring(0, resultSplit(1).length-1)
        println("Log Entries with regex pattern for time=" + time + " with delta=" + delta + " is " + count)
      }
      case Failure(response) => {
        println("Can't find count as the interval doesn't exist")
      }
    }
  }
}
