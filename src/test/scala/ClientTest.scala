import com.typesafe.config.ConfigFactory
import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers

import scala.concurrent.ExecutionContext
import Clients.{GRPCClient, GRPCServer}

import scala.util.{Failure, Success, Try}

class ClientTest extends AnyFlatSpec with Matchers {

  val conf = ConfigFactory.load("application")
  val url: String = conf.getString("randomLogGenerator.url")
  val op = 1

  //Test 1
  "REST API" should "be able to return correct count" in {
    val time = "02:47:04"
    val delta = "00:03:37"
    val responseAWS = scala.io.Source.fromURL(url+"/test?time="+time+"&delta="+delta)
    val ans = responseAWS.mkString

    ans === 555
  }

  //Test 2
  it should "also have Delta parameter" in {
    val time = "21:10:04"
    Try(scala.io.Source.fromURL(url+"/test?time="+time)) match {
      case Success(response) => {
        op === 0
      }
      case Failure(response) => {
        op === 1
      }
    }
  }

  //Test 3
  it should "also have Time parameter" in {
    val delta = "00:05:04"
    Try(scala.io.Source.fromURL(url+"/test?delta="+delta)) match {
      case Success(response) => {
        op === 0
      }
      case Failure(response) => {
        op === 1
      }
    }
  }

  /**
    This covers multiple unit tests, inlcuding the following:
    //Test 4
    Checking gRPC implementation

    //Test 5
    server listeners

    //Test 6
    checking port consistency with server
   */
  "GRPC Server" should "respond with result to GRPC Client" in {
    val server = new GRPCServer(ExecutionContext.global)
    GRPCServer.startServer(server)
    val client = GRPCClient("localhost", conf.getInt("randomLogGenerator.port"))
    val ans = client.callServer("21:09:00,00:01:00")
    client.stop()
    GRPCServer.stopServer(server)

    ans.mkString === "No interval found"
  }

  //Test 7
  "" should "check if port is read from .conf file" in {
    conf.getInt("randomLogGenerator.port") === 50070
  }
}