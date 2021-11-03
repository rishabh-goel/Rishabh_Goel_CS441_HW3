package Clients

import com.example.protos.hello.{LogFileAnalyzerGrpc, Input, Output}
import com.typesafe.config.ConfigFactory
import io.grpc.{Server, ServerBuilder}
import jdk.nashorn.internal.parser.JSONParser

import java.util.logging.Logger
import scala.concurrent.{ExecutionContext, Future}
import scala.util.*

object GRPCServer {
  val logger = Logger.getLogger(classOf[GRPCServer].getName)
  val conf = ConfigFactory.load("application")
  val port: Int = conf.getInt("randomLogGenerator.port")
  val url: String = conf.getString("randomLogGenerator.url")

  def main(args: Array[String]): Unit = {
    val server: GRPCServer = new GRPCServer(ExecutionContext.global)
    startServer(server)
    blockServerUntilShutdown(server)
  }

  def startServer(server: GRPCServer): Unit = {
    server.start()
  }

  def blockServerUntilShutdown(server: GRPCServer): Unit =  {
    server.blockUntilShutdown()
  }

  def stopServer(server: GRPCServer): Unit =  {
    server.stop()
  }
}

class GRPCServer(executionContext: ExecutionContext) { self =>
  private[this] var server: Server = _

  //Start the server
  def start(): Unit = {
    server = ServerBuilder.forPort(GRPCServer.port).addService(LogFileAnalyzerGrpc.bindService(new LogFileAnalyzerImpl, executionContext)).build.start
    GRPCServer.logger.info("Server started, listening on port: " + GRPCServer.port)
    sys.addShutdownHook {
      System.err.println("Shutting down gRPC server")
      self.stop()
      System.err.println("Server shut down")
    }
  }

  //Stop the server
  def stop(): Unit = {
    if (server != null) {
      server.shutdown()
    }
  }

  //Block Server Until Shoutdown
  def blockUntilShutdown(): Unit = {
    if (server != null) {
      server.awaitTermination()
    }
  }

  class LogFileAnalyzerImpl extends LogFileAnalyzerGrpc.LogFileAnalyzer {
    override def checkFunction(req: Input): Future[Output] = {

      //Read input parameters
      val params = req.timedelta.split(",")
      val time = params(0)
      val delta = params(1)

      //Call Lambda API Gateway
      Try(scala.io.Source.fromURL(GRPCServer.url+"/GRPC?time="+time+"&delta="+delta)) match {
        case Success(response) => {
          val result = response.mkString
          val reply = Output(message = result)
          response.close()
          Future.successful(reply)
        }
        case Failure(response) => {
          val result = "No interval found"
          val reply = Output(message = result)
          Future.successful(reply)
        }
      }
    }
  }
}
