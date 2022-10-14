import torch
import torch.nn as nn
import torch.nn.functional as F

class Embedding(nn.Module):
    def __init__(self, K, D):
        super().__init__()
        self.K = K
        self.embedding = nn.Embedding(K, D)
        self.embedding.weight.data.uniform_(-1./K, 1./K)

    def forward(self, x):
        # Reshape inputs from BCHW to BHWC
        x = x.permute(0, 2, 3, 1).contiguous()
        x_shape = x.shape

        flat_x = x.view(-1, self.embedding.weight.size(0))

        # Calculate distances to find the closest codebook vectors
        distances = (torch.sum(flat_x**2, dim=1, keepdim=True) 
                    + torch.sum(self.embedding.weight**2, dim=1)
                    - 2 * torch.matmul(flat_x, self.embedding.weight.t()))
        
        # We get the indices from argmin
        encoding_indices = torch.argmin(distances, dim=1)
        encodings = torch.zeros(encoding_indices.shape[0], self.K, device='cuda')
        encodings.scatter_(1, encoding_indices, 1)

        # Quantize the vector by multiplying the encodings with the embeddings
        quantized = torch.matmul(encodings, self.embedding.weight).view(x_shape)

        # Calculate the loss. Note that the paper has log likelihood as the
        # loss but minimising the mean squared error is equivalent.
        commit_loss = F.mse_loss(quantized.detach(), x)
        vq_loss = F.mse_loss(quantized, x.detach()) 
        
        quantized = x + (quantized - x).detach()

        return vq_loss + 1.0 * commit_loss, quantized.permute(0, 3, 1, 2).contiguous(), encodings, encoding_indices.squeeze()

class ResBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.net = nn.Sequential(
            nn.ReLU(True),
            nn.Conv2d(channels, channels, 3, 1, 1),
            nn.BatchNorm2d(channels),
            nn.ReLU(True),
            nn.Conv2d(channels, channels, 1),
            nn.BatchNorm2d(channels)
        )

    def forward(self, x):
        return x + self.net(x)


class Encoder(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 4, 2, 1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(True),
            nn.Conv2d(out_channels, out_channels // 2, 4, 2, 1),
            ResBlock(out_channels),
            ResBlock(out_channels),
        )

    def forward(self, x):
        return self.net(x)

class Decoder(nn.Module):
    def __init__(self, in_channels, out_channels):
        self.net = nn.Sequential(
            ResBlock(in_channels // 2),
            ResBlock(in_channels // 2),
            nn.ReLU(True),
            nn.ConvTranspose2d(in_channels // 2, in_channels, 4, 2, 1),
            nn.BatchNorm2d(dim),
            nn.ReLU(True),
            nn.ConvTranspose2d(in_channels, out_channels, 4, 2, 1),
            nn.Tanh()
        )

    def forward(self, x):
        return self.net(x)