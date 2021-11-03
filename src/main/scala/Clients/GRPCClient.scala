package Clients

import com.example.protos.hello.LogFileAnalyzerGrpc.LogFileAnalyzerBlockingStub
import com.example.protos.hello.{LogFileAnalyzerGrpc, Input}
import com.typesafe.config.ConfigFactory
import io.grpc.{ManagedChannel, ManagedChannelBuilder, StatusRuntimeException}

import java.util.concurrent.TimeUnit
import java.util.logging.{Level, Logger}

object GRPCClient {
  def apply(host: String, port: Int): GRPCClient = {
    //Creating a channel for communication between client and server
    val channel = ManagedChannelBuilder.forAddress(host, port).usePlaintext().build

    val blockingStub = LogFileAnalyzerGrpc.blockingStub(channel)
    new GRPCClient(channel, blockingStub)
  }

  def main(args: Array[String]): Unit = {
    val conf = ConfigFactory.load("application")

    //Fetching port number from application.conf
    val client = GRPCClient("localhost", conf.getInt("randomLogGenerator.port"))

    //If no input provided, take default input
    try {
      val user = args.headOption.getOrElse("21:00:00,00:01:00")
      println("Result is: "+client.callServer(user))
    } finally {
      client.stop()
    }
  }
}

class GRPCClient private(private val channel: ManagedChannel, private val blockingStub: LogFileAnalyzerBlockingStub) {
  val logger = Logger.getLogger(classOf[GRPCClient].getName)

  //Calling the server
  def callServer(time: String): String = {
    val params = time.split(",")
    logger.info("Sending " + params(0)+" "+ params(1)+ " from AWS Lambda function through API Gateway")
    val request = Input(timedelta = time)
    try {
      val response = blockingStub.checkFunction(request)
      logger.info("Result: " + response.message)
      response.message
    }
    catch {
      case e: StatusRuntimeException =>
        logger.log(Level.WARNING, "RPC failed: {0}", e.getStatus)
        "Failed to execute"
    }
  }

  //Shutting down the channel
  def stop(): Unit = {
    channel.shutdown.awaitTermination(5, TimeUnit.SECONDS)
  }
}
